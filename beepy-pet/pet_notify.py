#!/usr/bin/env python3
"""Page the owner (via the beepy-pager ntfy topic) when the pet needs care.

Run every 15 minutes by beepy-pet-notify.timer as root, because the ntfy topic lives
in the root-only /etc/beepy-pager.conf. It only reads the pet's save file and never
writes it, so it can't race with the game. Pages carry the "pet" tag, which the
pager shows in pink.
"""

import json
import os
import sys
import time
import urllib.request

PET_STATE = "/home/pi/.local/share/beepy-pet/state.json"
PAGER_CONF = "/etc/beepy-pager.conf"
COOLDOWN_FILE = "/var/lib/beepy-pet/last-pages.json"
COOLDOWN = 3 * 3600        # page about the same need at most every 3 hours
QUIET_HOURS = (22, 8)      # no pages from 10pm to 8am

MESSAGES = {
    "sick": "{n} feels sick and needs medicine [m]",
    "hungry": "{n}'s tummy is rumbling. Feed me? [f]",
    "lonely": "{n} misses you. A hug? [h]",
    "tired": "{n} can barely keep their eyes open [s]",
    "dirty": "{n}'s room is getting stinky [c]",
    "gone": "{n} went to stay with Grandma. There's a note.",
}


def load_pet():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import pet_state
    with open(PET_STATE) as f:
        pet = pet_state.Pet(**json.load(f))
    pet.advance()  # in memory only: see where the stats are right now
    return pet


def pager_conf():
    conf = {"SERVER": "https://ntfy.sh"}
    with open(PAGER_CONF) as f:
        for line in f:
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.strip().split("=", 1)
                conf[k] = v.strip('"')
    return conf


def quiet(hour):
    start, end = QUIET_HOURS
    return hour >= start or hour < end


def main():
    try:
        pet = load_pet()
    except FileNotFoundError:
        return  # no pet yet
    if pet.stage() == "egg":
        return
    needs = ["gone"] if pet.ran_away else pet.needs()
    if not needs or quiet(time.localtime().tm_hour):
        return

    try:
        with open(COOLDOWN_FILE) as f:
            last = json.load(f)
    except (FileNotFoundError, ValueError):
        last = {}
    now = time.time()
    need = needs[0]  # most urgent only: one page at a time
    key = f"{pet.born}:{need}"  # a new pet starts with fresh cooldowns
    if now - last.get(key, 0) < (10 * 365 * 86400 if need == "gone" else COOLDOWN):
        return

    conf = pager_conf()
    body = json.dumps({"topic": conf["TOPIC"], "title": f"♥ {pet.name}",
                       "message": MESSAGES[need].format(n=pet.name), "tags": ["pet"]}).encode()
    req = urllib.request.Request(conf["SERVER"].rstrip("/"), data=body,
                                 headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=30).close()
    print(f"paged: {need}")

    last[key] = now
    os.makedirs(os.path.dirname(COOLDOWN_FILE), exist_ok=True)
    with open(COOLDOWN_FILE, "w") as f:
        json.dump(last, f)


if __name__ == "__main__":
    main()
