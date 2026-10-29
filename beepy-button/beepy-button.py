#!/usr/bin/env python3
"""Beepy side button (GPIO 17): single press shows `home`, double press opens `pet`.

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
MARKER = "/tmp/beepy-button-popup"  # exists while a popup we opened is showing
# home draws once and exits, so wait for a key to keep the snapshot on screen.
APPS = {"home": "home; read -rsn1", "pet": "pet"}


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


def count_presses(req):
    """After a first press, count further presses inside the double-press window."""
    presses, last = 1, time.monotonic()
    deadline = last + DOUBLE_PRESS_S
    while (remaining := deadline - time.monotonic()) > 0 and req.wait_edge_events(remaining):
        for _ in req.read_edge_events():
            now = time.monotonic()
            if now - last >= DEBOUNCE_S:
                presses, last = presses + 1, now
    return presses


def main():
    settings = gpiod.LineSettings(direction=Direction.INPUT, bias=Bias.PULL_UP, edge_detection=Edge.FALLING)
    with gpiod.request_lines(CHIP, consumer="beepy-button", config={LINE: settings}) as req:
        print(f"watching GPIO {LINE}", flush=True)
        while True:
            req.read_edge_events()  # blocks until the first press
            presses = count_presses(req)
            client = first_client()
            if client is None:
                print("button: no tmux client, nothing to show", flush=True)
            elif presses >= 2:
                on_double(client)
            else:
                on_single(client)


if __name__ == "__main__":
    main()
