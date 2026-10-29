#!/usr/bin/env python3
"""Beepy side button (GPIO 17): single press shows `home`, double press opens `pet`,
hold (~1 s) opens the PicoClaw AI assistant in its own tmux window (scrollable).

The button shorts GPIO 17 to ground, so the line uses the Pi's internal pull-up and a
press is a falling edge. Apps open as a full-screen tmux popup over whatever is on the
screen; pressing again (or the app's own exit key) closes it. If `pet` is already
running in a tmux window, a double press jumps there instead of starting a second
copy, which would overwrite the first one's save.
"""

import os
import subprocess
import time

import gpiod
from gpiod.line import Bias, Direction, Edge

CHIP = "/dev/gpiochip0"
LINE = 17
DEBOUNCE_S = 0.08      # contact bounce is a few ms; presses are ~150 ms apart at the fastest
DOUBLE_PRESS_S = 0.4   # a second press within this window makes it a double press
HOLD_S = 0.8           # still pressed after this long = a hold
MARKER = "/tmp/beepy-button-popup"  # exists while a popup we opened is showing
CLAW_WINDOW = "claw"  # tmux window name for PicoClaw
# home draws once and exits, so wait for a key to keep the snapshot on screen.
APPS = {
    "home": "home; read -rsn1",
    "pet": "pet",
    # If PicoClaw exits with an error (e.g. no API key yet), keep the message on screen.
    "claw": "claw || { echo; echo 'PicoClaw stopped (run set-claude-key?)'; "
            "echo 'Press any key to close.'; read -rsn1; }",
}


def tmux(*args):
    return subprocess.run(["tmux", *args], capture_output=True, text=True)


def first_client():
    """The tmux client on the Beepy's screen (tty1), or None when tmux isn't running."""
    clients = tmux("list-clients", "-F", "#{client_name}").stdout.split()
    tty_clients = [c for c in clients if c.startswith("/dev/tty")]
    return (tty_clients or clients or [None])[0]


def close_popup(client):
    """Close our popup if one is open. Returns True if there was one."""
    if not os.path.exists(MARKER):
        return False
    tmux("display-popup", "-C", "-c", client)
    os.remove(MARKER)
    return True


def open_popup(client, app):
    cmd = f"touch {MARKER}; {APPS[app]}; rm -f {MARKER}"
    # -b none: no border, so the app's 50x13 layout fills the screen exactly.
    tmux("display-popup", "-c", client, "-E", "-b", "none", "-w", "100%", "-h", "100%", cmd)
    print(f"button: opened {app}", flush=True)


def running_pet_window():
    """tmux window ("session:index") where `pet` already runs, or None."""
    pids = subprocess.run(["pgrep", "-f", "beepy-pet/pet_app.py"], capture_output=True, text=True).stdout.split()
    parents = set()
    for pid in pids:
        try:
            with open(f"/proc/{pid}/stat") as f:
                parents.add(f.read().rsplit(")", 1)[1].split()[1])  # ppid: the shell in the pane
        except OSError:
            pass
    for line in tmux("list-panes", "-a", "-F", "#{pane_pid} #{session_name}:#{window_index}").stdout.splitlines():
        pane_pid, window = line.split()
        if pane_pid in parents:
            return window
    return None


def on_single(client):
    if close_popup(client):
        print("button: closed popup", flush=True)
    else:
        open_popup(client, "home")


def on_double(client):
    close_popup(client)
    window = running_pet_window()
    if window:
        tmux("switch-client", "-c", client, "-t", window)
        print(f"button: pet already running, switched to {window}", flush=True)
    else:
        open_popup(client, "pet")


def on_hold(client):
    """PicoClaw runs in its own tmux window (not a popup) so long answers keep scrollback."""
    close_popup(client)
    window = tmux("list-windows", "-a", "-F", "#{session_name}:#{window_index} #{window_name}").stdout
    existing = [line.split()[0] for line in window.splitlines() if line.split()[1:] == [CLAW_WINDOW]]
    if existing:
        tmux("switch-client", "-c", client, "-t", existing[0])
        print(f"button: switched to {existing[0]}", flush=True)
        return
    session = tmux("display-message", "-p", "-c", client, "#{session_name}").stdout.strip()
    tmux("new-window", "-t", f"{session}:", "-n", CLAW_WINDOW, APPS["claw"])
    print("button: opened claw window", flush=True)


def is_press(event):
    return event.event_type == event.Type.FALLING_EDGE


def released_within(req, seconds):
    """Wait up to `seconds` for the button to be let go. True if it was released."""
    deadline = time.monotonic() + seconds
    while (remaining := deadline - time.monotonic()) > 0 and req.wait_edge_events(remaining):
        if any(not is_press(e) for e in req.read_edge_events()):
            return True
    return False


def count_presses(req):
    """After a first press (already released), count further presses in the double-press window."""
    presses, last = 1, time.monotonic()
    deadline = last + DOUBLE_PRESS_S
    while (remaining := deadline - time.monotonic()) > 0 and req.wait_edge_events(remaining):
        for e in req.read_edge_events():
            now = time.monotonic()
            if is_press(e) and now - last >= DEBOUNCE_S:
                presses, last = presses + 1, now
    return presses


def main():
    # Both edges: presses (falling) and releases (rising), so a hold can be told from a tap.
    settings = gpiod.LineSettings(direction=Direction.INPUT, bias=Bias.PULL_UP, edge_detection=Edge.BOTH)
    with gpiod.request_lines(CHIP, consumer="beepy-button", config={LINE: settings}) as req:
        print(f"watching GPIO {LINE}", flush=True)
        while True:
            if not any(is_press(e) for e in req.read_edge_events()):  # blocks; skip stray releases
                continue
            held = not released_within(req, HOLD_S)
            client = first_client()
            if held:  # open right away while still held, then wait for the release
                on_hold(client) if client else print("button: no tmux client", flush=True)
                released_within(req, 30)
                continue
            presses = count_presses(req)
            if client is None:
                print("button: no tmux client, nothing to show", flush=True)
            elif presses >= 2:
                on_double(client)
            else:
                on_single(client)


if __name__ == "__main__":
    main()
