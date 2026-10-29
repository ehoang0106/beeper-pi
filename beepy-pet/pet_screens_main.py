"""Main pet screen (day room, night room, egg) drawn into a Canvas.

Layout on the 50x13 grid, matching the `home` screen:
  row 0 header bar · rows 1-8 room (cols 0-23) + stats panel (cols 25-48)
  row 9 floor rule · row 10 status · row 11 action bar · row 12 footer
"""

import pet_art
import pet_state
from pet_canvas import BOLD, NORMAL, REV, REV_BOLD, W

FOOTER = " pet  ·  i stats  ·  q quit  ·  End Call: menu"
STARS = [(1, 2, "°"), (1, 14, "·"), (2, 9, "·"), (3, 3, "·"), (5, 21, "°"), (7, 1, "·")]
POOP_SLOTS = [20, 2]  # floor columns for the 1st and 2nd poop pile (row 8)
BADGE_ORDER = ["SICK", "HUNGRY", "TIRED", "DIRTY", "SAD", "POOP"]


def fmt_age(seconds):
    m = int(seconds // 60)
    if m < 60:
        return f"{m}m"
    h, m = divmod(m, 60)
    if h < 24:
        return f"{h}h {m:02d}m"
    d, h = divmod(h, 24)
    return f"{d}d {h:02d}h"


def header(c, name, suffix="", right=""):
    c.bar(0)
    c.text(0, 0, " ■ ", REV)
    c.text(0, 3, name, REV_BOLD)
    c.text(0, 3 + len(name), suffix, REV)
    c.text(0, W - len(right), right, REV)


def rule(c, row=9):
    c.text(row, 1, "─" * 48)


def footer(c, text):
    c.text(12, 0, text)


def status(c, glyph, text):
    c.text(10, 1, glyph, BOLD)
    c.text(10, 3, text[:46])


def action_bar(c, items, pressed=None):
    """items: [(key, label, enabled)]; enabled keys get a reverse keycap."""
    col = 1
    for key, label, enabled in items:
        c.text(11, col, key, REV if enabled and key != pressed else NORMAL)
        c.text(11, col + 2, label)
        col += 2 + len(label) + 3


def badges(pet):
    """Warning badges in priority order, each with a 'critical' flag for blinking."""
    found = []
    if pet.sick:
        found.append(("SICK", True))
    for stat, name in (("fullness", "HUNGRY"), ("energy", "TIRED"), ("clean", "DIRTY"), ("happy", "SAD")):
        v = getattr(pet, stat)
        if v < 25:
            found.append((name, v < 10))
    if pet.poops:
        found.append(("POOP", False))
    found.sort(key=lambda b: BADGE_ORDER.index(b[0]))
    return found


def stats_panel(c, pet, t):
    for row, (label, stat) in enumerate((("FULL", "fullness"), ("HAPPY", "happy"),
                                         ("ENERGY", "energy"), ("CLEAN", "clean")), start=2):
        v = round(getattr(pet, stat))
        c.text(row, 25, f"{label:<6}", BOLD if v < 25 else NORMAL)
        c.text(row, 32, f"{pet_art.meter(v, 12)} {v:>3}")
    if pet.asleep:
        c.text(7, 25, f"zZ asleep {fmt_age(pet.asleep_for())}", BOLD)
        return
    col = 25
    shown = badges(pet)
    for name, critical in shown[:2]:
        blink_off = critical and (t // 2) % 2 == 1
        c.text(7, col, f" {name} ", NORMAL if blink_off else REV_BOLD)
        col += len(name) + 3
    if len(shown) > 2:
        c.text(7, col, f"+{len(shown) - 2}")


def draw_room(c, app):
    """Pet, particles, poop and (at night) the dark room card."""
    pet, t = app.pet, app.t
    stage = pet.stage()
    x, y = pet_art.sprite_pos(stage)
    x += app.idle_dx
    y -= app.hop
    night = pet.asleep and app.effect_name != "wake"
    if night:
        c.fill(1, 0, 24, 8, REV)
        for r, col, ch in STARS:
            twinkle = {"·": "°", "°": "·"}[ch] if (r + col + t // 3) % 7 == 0 else ch
            c.text(r, col, twinkle, REV)

    face, particles = app.face_and_particles(stage, x, y)
    w = len(pet_art.TEMPLATES[stage][0])
    if app.effect_name == "refuse":
        x += 1 if t % 2 == 0 else -1
    c.sprite(y, x, pet_art.sprite(stage, face, blink=app.blinking()), BOLD, pet_art.MASKS[stage])
    attr = REV if night else NORMAL
    for dy, dx, glyph in particles:
        _particle(c, y + dy, x + dx, glyph, attr)

    for i in range(min(pet.poops, 2)):
        col = POOP_SLOTS[i]
        c.text(8, col, "▄█▄", BOLD | (REV if night else NORMAL))
        stink = "° °" if t % 2 == 0 else " ° "
        c.text(7, col, stink, attr)
    _mood_ambient(c, app, stage, x, y, w, attr)


def _particle(c, row, col, glyph, attr):
    """Draw a particle inside the room: pinned below the header, never into the panel."""
    if col >= 0 and col + len(glyph) <= 24:
        c.text(max(1, row), col, glyph, attr)


def _mood_ambient(c, app, stage, x, y, w, attr):
    """Two-frame loops that show the mood without reading the panel."""
    if app.effect_name:
        return
    mood, frame = app.pet.mood(), app.t % 2
    if mood == "hungry":
        c.text(max(1, y - 2), x + w, "(▲)", attr)
        c.text(max(1, y - 1), x + w - 1, "°", attr)
    elif mood == "happy":
        notes = [((1, 3, "♪"), (1, 20, "♫")), ((1, 19, "♫"), (1, 5, "♪"))][frame]
        for r, col, ch in notes:
            c.text(r, col, ch, attr)
    elif mood == "dirty":
        flies = [((1, 16, "·"), (1, 4, "°")), ((1, 6, "·"), (1, 18, "°"))][frame]
        for r, col, ch in flies:
            c.text(r, col, ch, attr)
    elif mood == "sick":
        _particle(c, y - 2, x + 3, "≈", attr)
        r, col = (y - 1, x + w - 3) if frame == 0 else (y + 1, x + w)
        _particle(c, r, col, "°", attr)
    elif mood == "sleeping":
        step = (app.t // 2) % 3
        zs = [[(-1, w - 1, "z")], [(-2, w, "z"), (-3, w + 2, "Z")], [(-1, w - 1, "z"), (-3, w + 3, "Z")]][step]
        for dy, dx, ch in zs:
            _particle(c, y + dy, x + dx, ch, attr)


def draw_main(c, app):
    pet = app.pet
    stage = pet.stage()
    if stage == "egg":
        return draw_egg(c, app)
    header(c, pet.name, right=f"{stage.upper()} · {fmt_age(pet.age_seconds())} ")
    draw_room(c, app)
    stats_panel(c, pet, app.t)
    rule(c)
    status(c, *app.status_line())
    awake = not pet.asleep
    last = ("m", "meds", True) if pet.sick else ("h", "hug", True)
    action_bar(c, [("f", "feed", awake), ("p", "play", awake),
                   ("s", "sleep" if awake else "wake ", True), ("c", "clean", awake), last],
               app.pressed_key())
    footer(c, FOOTER)


def draw_egg(c, app):
    pet = app.pet
    hatching = pet.stage() != "egg"  # the hatch animation plays just after the stage flips
    left = 0 if hatching else pet.next_stage_in()
    header(c, pet.name, right="EGG · hatching! " if hatching else f"EGG · {max(1, round(left / 60))}m left ")
    frame = app.egg_frame()
    x, _ = pet_art.sprite_pos("egg")
    c.sprite(9 - len(frame), x, frame, BOLD)  # bottom-aligned: the lid frame is a row taller
    c.text(3, 17, "°" if app.t % 4 < 2 else " ")
    c.text(4, 6, "·")
    pct = round(100 * (1 - left / pet_state.EGG_SECONDS))
    c.text(2, 25, f"HATCH  {pet_art.meter(pct, 12)} {pct:>2}%")
    c.text(4, 25, "keep it cozy & close")
    c.text(5, 25, "pat it to say hello")
    rule(c)
    status(c, *app.status_line())
    action_bar(c, [("h", "pat the egg", True)], app.pressed_key())
    footer(c, FOOTER)

