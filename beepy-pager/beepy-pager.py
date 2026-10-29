#!/usr/bin/env python3
"""Beepy pager: subscribe to an ntfy topic and signal new messages on the RGB LED.

A message blinks the LED in a priority color, then keeps it lit until the next
keypress. The message text is broadcast to the Beepy's terminals with `wall`.
Config is read from /etc/beepy-pager.conf (TOPIC=..., SERVER=..., optional GMAIL_URL=...).

If GMAIL_URL is set, the Gmail Apps Script web app is also polled every minute and
new inbox mail pages at low priority (green). Gmail doesn't go through ntfy.sh because
ntfy.sh's free per-IP quota is shared by every Apps Script on Google's servers.
"""

import json
import subprocess
import threading
import time
import urllib.request

CONF_PATH = "/etc/beepy-pager.conf"
SYSFS = "/sys/firmware/beepy"

# ntfy priority (1 min .. 5 urgent) -> LED color (r, g, b)
PRIORITY_COLORS = {
    5: (255, 0, 0),    # urgent: red
    4: (255, 80, 0),   # high: orange
    3: (0, 0, 255),    # default: blue
    2: (0, 255, 0),    # low: green
    1: (0, 255, 0),    # min: green
}
# ntfy tag -> LED color, overriding priority (pet pages from beepy-pet are pink).
TAG_COLORS = {"pet": (255, 40, 140)}

WIFI_DOWN_COLOR = (255, 0, 0)  # red while wlan0 has no link
WIFI_CARRIER = "/sys/class/net/wlan0/carrier"
WIFI_POLL_SECONDS = 3
WIFI_DOWN_POLLS = 2  # ~6 s without link before going red, so brief blips don't flash

# Monotonic time of the newest unacknowledged message (None = nothing pending), its
# color, and whether Wi-Fi is down. show_led() turns these into the LED state.
pending_since = None
pending_color = None
wifi_down = False
lock = threading.Lock()


def load_conf():
    conf = {"SERVER": "https://ntfy.sh"}
    with open(CONF_PATH) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                conf[key.strip()] = value.strip().strip('"')
    return conf


def write_sysfs(name, value):
    with open(f"{SYSFS}/{name}", "w") as f:
        f.write(str(value))


def set_led(color):
    """Turn the LED on with an (r, g, b) color, or off when color is None."""
    if color is None:
        write_sysfs("led", 0)
        return
    for name, level in zip(("led_red", "led_green", "led_blue"), color):
        write_sysfs(name, level)
    write_sysfs("led", 1)


def show_led():
    """Apply the LED state; call with `lock` held. Wi-Fi down beats a pending page."""
    if wifi_down:
        set_led(WIFI_DOWN_COLOR)
    elif pending_since is not None:
        set_led(pending_color)
    else:
        set_led(None)


def ms_since_keypress():
    with open(f"{SYSFS}/last_keypress") as f:
        return int(f.read().strip())


def printable(text):
    # Messages come from the network: drop control chars before they reach a terminal.
    return "".join(c for c in text if c.isprintable() or c == "\n")


def on_message(msg):
    global pending_since, pending_color
    color = PRIORITY_COLORS.get(msg.get("priority", 3), PRIORITY_COLORS[3])
    for tag in msg.get("tags", []):
        color = TAG_COLORS.get(tag, color)
    title = printable(msg.get("title", "")).strip()
    body = printable(msg.get("message", "")).strip()
    text = f"[{title}] {body}" if title else body
    print(f"message p{msg.get('priority', 3)}: {text}", flush=True)
    subprocess.run(["wall", "-n", f"PAGE: {text}"], check=False)

    with lock:
        pending_since, pending_color = time.monotonic(), color
    for _ in range(3):
        set_led(color)
        time.sleep(0.25)
        set_led(None)
        time.sleep(0.25)
    with lock:
        show_led()


def clear_on_keypress():
    """Turn the LED off once a key has been pressed after the pending message arrived."""
    global pending_since
    while True:
        time.sleep(1)
        with lock:
            if pending_since is None:
                continue
            waited_ms = (time.monotonic() - pending_since) * 1000
            if ms_since_keypress() < waited_ms:
                pending_since = None
                show_led()


def link_up():
    try:
        with open(WIFI_CARRIER) as f:
            return f.read().strip() == "1"
    except OSError:
        return False  # interface down or missing: no link


def watch_wifi():
    """Turn the LED red while Wi-Fi is disconnected, and restore it when it's back."""
    global wifi_down
    down_polls = 0
    while True:
        down_polls = 0 if link_up() else down_polls + 1
        now_down = down_polls >= WIFI_DOWN_POLLS
        if now_down != wifi_down:
            with lock:
                wifi_down = now_down
                show_led()
            print("wifi disconnected: LED red" if now_down else "wifi back: LED restored", flush=True)
        time.sleep(WIFI_POLL_SECONDS)


def subscribe(conf):
    url = f"{conf['SERVER'].rstrip('/')}/{conf['TOPIC']}/json"
    backoff = 5
    # After a dropout, ask ntfy to replay anything sent since then: the last message id
    # seen, or the first connect time (unix seconds) if no message has arrived yet.
    since = None
    while True:
        try:
            # ntfy sends a keepalive every ~45s, so a 90s read timeout detects dead links.
            full_url = f"{url}?since={since}" if since else url
            with urllib.request.urlopen(full_url, timeout=90) as resp:
                print(f"subscribed to {full_url}", flush=True)
                backoff = 5
                for line in resp:
                    event = json.loads(line)
                    if event.get("event") == "open" and since is None:
                        since = event["time"]
                    elif event.get("event") == "message":
                        since = event["id"]
                        on_message(event)
        except Exception as e:
            print(f"connection lost ({e}), retrying in {backoff}s", flush=True)
            time.sleep(backoff)
            backoff = min(backoff * 2, 300)


def poll_gmail(url):
    """Poll the Gmail web app every minute and page for inbox messages not seen before."""
    seen = {}  # message id -> unix time it was first seen, pruned after a day
    first_poll = True
    since = int(time.time())
    while True:
        try:
            # Look back 10 extra minutes so delayed deliveries aren't missed; seen ids stop repeats.
            with urllib.request.urlopen(f"{url}&since={since - 600}", timeout=60) as resp:
                data = json.load(resp)
            if "error" in data:
                raise RuntimeError(data["error"])
            for msg in data["messages"]:
                if msg["id"] in seen:
                    continue
                seen[msg["id"]] = time.time()
                # The first poll only records what is already there instead of paging for it.
                if not first_poll:
                    on_message({"priority": 2, "title": f"✉ {msg['from']}", "message": msg["subject"]})
            first_poll = False
            since = int(time.time())
            seen = {k: t for k, t in seen.items() if t > since - 86400}
        except Exception as e:
            print(f"gmail poll failed ({e})", flush=True)
        time.sleep(60)


def main():
    conf = load_conf()
    set_led(None)
    threading.Thread(target=clear_on_keypress, daemon=True).start()
    threading.Thread(target=watch_wifi, daemon=True).start()
    if conf.get("GMAIL_URL"):
        threading.Thread(target=poll_gmail, args=(conf["GMAIL_URL"],), daemon=True).start()
    subscribe(conf)


if __name__ == "__main__":
    main()
