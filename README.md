# beeper-pi

Small programs for the **Beepy** (Beeper × SQFMI handheld: Raspberry Pi Zero 2 W, Sharp
memory LCD, BlackBerry keyboard, RGB LED, programmable side button) running Raspberry Pi
OS Lite. Everything is plain Python 3 / bash with no extra packages, designed for the
console's 50×13 text screen and its CP437 font.

| Folder | What it does |
|---|---|
| [`beepy-pager/`](beepy-pager) | Turns the RGB LED into a pager: ntfy.sh pages, Outlook and Gmail mail alerts |
| [`beepy-pet/`](beepy-pet) | **Mochi**, a Shaun-the-Sheep-inspired virtual pet with mini-games |
| [`beepy-button/`](beepy-button) | Side button: press once for `home`, double-press for `pet`, hold for PicoClaw |
| [`beepy-claw/`](beepy-claw) | Helpers to run the [PicoClaw](https://github.com/sipeed/picoclaw) AI assistant with Claude |
| [`beepy-home/`](beepy-home) | The `home` status screen and a neofetch config that fit the small screen |

## beepy-pager

A systemd service that subscribes to an [ntfy](https://ntfy.sh) topic and flashes the LED
when a page arrives. The LED stays lit until a key is pressed, and the text is shown on
the terminal with `wall`.

- **LED colour** follows the ntfy priority: urgent = red, high = orange, default = blue,
  low = green. Pages tagged `pet` (from Mochi) are pink.
- **Missed pages** sent during a Wi-Fi dropout are replayed when it reconnects (ntfy keeps
  messages for 12 h).
- **Gmail**: [`gmail-inbox-web-app.gs`](beepy-pager/gmail-inbox-web-app.gs) is a Google
  Apps Script web app that lists new Primary-tab mail (sender + subject only). The pager
  polls it every minute and pages green. It goes through the web app instead of ntfy
  because ntfy.sh's free quota is per IP and Apps Script shares Google's IPs.
- **Outlook**: a Power Automate flow ("When a new email arrives" → "Send an email" to
  `ntfy-<topic>@ntfy.sh`) pages blue. Note ntfy.sh only accepts 5 e-mails/day per sender IP.
- **Wi-Fi watch**: the LED turns solid red after ~6 s without a `wlan0` link, and goes back
  to off (or an unread page's colour) when it reconnects.

Send a page from anywhere:

```bash
curl -d "Build finished" ntfy.sh/<your-topic>
curl -H "Priority: urgent" -H "Title: Server" -d "Disk full!" ntfy.sh/<your-topic>
```

## beepy-pet (Mochi)

A Tamagotchi-style sheep. Run `pet`.

- **Grows up** in real time: woolly egg → baby (bead-art lamb) → teen → adult (Shaun).
- **Stats** (fullness, happy, energy, clean) keep dropping while the game is closed; the
  game catches up from the save file when it opens.
- **Keys**: `f` feed · `p` play · `s` sleep/wake · `c` clean · `h` hug · `m` medicine ·
  `i` stats · `q` quit.
- **Mini-games** (`p`): *Which paw?* (guess the hidden treat), *Sheep Train* (snake: lead
  lost lambs, `WASD` or touchpad), *Higher or Lower* (cards, `H` / `L`). Best scores are saved.
- **LED** shows the mood for 3 s when it changes, then goes dark to save battery; it stays
  off while Mochi sleeps.
- **Pages you** (pink) when it's hungry, lonely, tired, dirty or sick: at most once per
  need every 3 h, never between 10 pm and 8 am (`beepy-pet-notify.timer`).
- Neglected for 2 days, it leaves for Grandma's and writes you a note. It never dies.
- `pet --status` prints a one-line summary (used by `home`).

Run the tests (on a laptop or the Beepy):

```bash
cd beepy-pet && python3 -m unittest test_pet_state test_pet_new_games test_pet_render
```

## beepy-button

The side button is wired to **GPIO 17** (active low, needs the internal pull-up). A small
service waits for presses with `gpiod`:

- **single press**: show `home` as a full-screen tmux popup (any key closes it)
- **double press**: open `pet` as a popup, or jump to the tmux window where `pet` already runs
- **hold (~1 s)**: open the PicoClaw AI assistant (`picoclaw agent`) as a popup

## beepy-claw (PicoClaw + Claude)

[PicoClaw](https://github.com/sipeed/picoclaw) by Sipeed is a tiny AI-assistant program
(single Go binary, ~10-20 MB RAM) that runs fine on the Pi Zero 2 W; the model runs in the
cloud. Install `picoclaw_armv7.deb` from its releases, run `picoclaw onboard`, then:

- [`set-claude-key`](beepy-claw/set-claude-key): asks for your Claude API key with hidden
  input and stores it in `~/.picoclaw/.security.yml` (never on screen or in shell history).
- [`claude-param-proxy.py`](beepy-claw/claude-param-proxy.py): PicoClaw v0.3.1 always sends
  `temperature`, which Claude Sonnet/Haiku 5.5 reject. This localhost-only relay
  (`127.0.0.1:8787`) strips that field and forwards everything else to api.anthropic.com,
  streaming included. Point the Claude models' `api_base` at `http://127.0.0.1:8787/v1`.
  Remove it once PicoClaw stops sending `temperature`.

Models configured in `~/.picoclaw/config.json`: `claude` (claude-sonnet-5-5, default) and
`claude-fast` (claude-haiku-5-5). PicoClaw's tools stay inside `~/.picoclaw/workspace`.

## beepy-home

- [`home`](beepy-home/home): clock, weather, battery, Wi-Fi + IP, a one-line pet summary
  and system stats on one 50×13 screen. `home -w` refreshes every 30 s.
- [`neofetch-config.conf`](beepy-home/neofetch-config.conf): no logo, short values, one
  screenful, plus a battery line read from the Beepy firmware.

## Install on a Beepy

Copy the repo to the Beepy, then:

```bash
# LED access for the pi user (the keyboard driver owns /sys/firmware/beepy)
echo "options beepy_kbd sysfs_gid=$(getent group gpio | cut -d: -f3)" | sudo tee /etc/modprobe.d/beepy-kbd-sysfs-gid.conf

# Pager (needs your own ntfy topic and, optionally, the Gmail web app URL)
sudo install -m 600 beepy-pager/beepy-pager.conf.example /etc/beepy-pager.conf   # then edit it
sudo install -m 755 beepy-pager/beepy-pager.py /usr/local/bin/beepy-pager
sudo install -m 644 beepy-pager/beepy-pager.service /etc/systemd/system/

# Pet
sudo mkdir -p /usr/local/lib/beepy-pet
sudo install -m 644 beepy-pet/*.py /usr/local/lib/beepy-pet/
sudo install -m 755 beepy-pet/pet /usr/local/bin/pet
sudo install -m 644 beepy-pet/beepy-pet-notify.service beepy-pet/beepy-pet-notify.timer /etc/systemd/system/

# Side button
sudo install -m 755 beepy-button/beepy-button.py /usr/local/bin/beepy-button
sudo install -m 644 beepy-button/beepy-button.service /etc/systemd/system/

# PicoClaw helpers (after installing picoclaw_armv7.deb and running `picoclaw onboard`)
sudo install -m 755 beepy-claw/set-claude-key /usr/local/bin/set-claude-key
sudo install -m 755 beepy-claw/claude-param-proxy.py /usr/local/bin/claude-param-proxy
sudo install -m 644 beepy-claw/claude-param-proxy.service /etc/systemd/system/

# Home screen + neofetch
sudo install -m 755 beepy-home/home /usr/local/bin/home
install -D -m 644 beepy-home/neofetch-config.conf ~/.config/neofetch/config.conf

sudo systemctl daemon-reload
sudo systemctl enable --now beepy-pager beepy-pet-notify.timer beepy-button claude-param-proxy
sudo reboot   # applies the LED permission
```

The services expect the `pi` user, NetworkManager, tmux on tty1 and the stock Beepy
packages (`beepy-kbd`, `sharp-drm`).

## Secrets

`/etc/beepy-pager.conf` holds the ntfy topic (anyone who knows it can page you) and the
Gmail web-app URL with its key. It is never committed: the repo only has
[`beepy-pager.conf.example`](beepy-pager/beepy-pager.conf.example), and the Apps Script's
`SECRET` is a placeholder here; set the real value in your deployed script.

## Credits

Mochi's sheep is fan art inspired by *Shaun the Sheep* (© Aardman Animations), made for
personal use.
