"""Secondary screens: the "Which paw?" mini-game, naming, stats and the grandma note."""

import time

import pet_art
import pet_copy
from pet_canvas import BOLD, NORMAL, REV, REV_BOLD, W
from pet_screens_main import fmt_age, footer, header, rule, status

CARD = ["┌───────┐", "│       │", "│   {}   │", "│       │", "└───────┘"]
CARD_COLS = {"l": 3, "r": 38}


def pips(results, rounds=5):
    marks = ["♥" if ok else "○" for ok in results] + ["·"] * (rounds - len(results))
    return " ".join(marks)


def draw_pet_center(c, stage, face, center=25):
    rows = pet_art.EGG if stage == "egg" else pet_art.sprite(stage, face)
    x, y = center - (len(rows[0]) + 1) // 2, 9 - len(rows)
    c.sprite(y, x, rows, BOLD, pet_art.MASKS.get(stage))


def draw_play(c, app):
    g, pet = app.game, app.pet
    stage = pet.stage()
    if g.phase == "intro":
        header(c, pet.name, " · play", "WHICH PAW? ")
        draw_pet_center(c, stage, "happy")
        for r, line in enumerate((f"{pet.name} hides a", "treat ▲ in one", "paw. Guess it!"), start=3):
            c.text(r, 2, line)
        for r, line in enumerate(("5 rounds", "3 to win", "+HAPPY ♥"), start=3):
            c.text(r, 36, line)
        rule(c)
        status(c, "♪", f"{pet.name} is ready to play!")
        c.text(11, 1, "p", REV)
        c.text(11, 3, "start")
        footer(c, " play  ·  any key: start  ·  q back")
        return
    if g.phase == "end":
        return _draw_play_end(c, app)

    header(c, pet.name, " · play", f"round {g.round}/5 ")
    face = {"reveal": "happy" if g.correct else "tease"}.get(g.phase, "content")
    draw_pet_center(c, stage, face)
    for side, col in CARD_COLS.items():
        if g.phase == "shuffle":
            mark = "▲" if side == g.treat else " "
        elif g.phase == "guess":
            mark = "?"
        else:
            mark = "▲" if side == g.treat else "·"
        chosen = g.phase == "reveal" and side == g.choice
        for r, line in enumerate(CARD, start=3):
            c.text(r, col, line.format(mark), REV_BOLD if chosen else NORMAL)
    if g.phase == "guess":
        c.text(1, 16, "which paw? hmm...", BOLD)
        c.text(8, 5, "l", REV)
        c.text(8, 7, "left")
        c.text(8, 39, "r", REV)
        c.text(8, 41, "right")
    elif g.phase == "shuffle":
        c.text(1, 17, "watch closely...", BOLD)
    else:
        if g.correct:
            c.text(1, 22, "♪  ♫")
        c.text(8, 37, "√ found it!" if g.correct else "  nope!", BOLD)
    rule(c)
    c.text(10, 1, f"score  {pips(g.results)}")
    c.text(10, 34, "need 3 to win")
    footer(c, " next round in a sec..." if g.phase == "reveal" else " l left  ·  r right  ·  q give up")


def _draw_play_end(c, app):
    g, pet = app.game, app.pet
    won = sum(g.results) >= 3
    header(c, pet.name, " · play", f"{sum(g.results)} / 5 ")
    word = pet_art.big_text("YAY!" if won else "OOPS")
    col = (W - len(word[0])) // 2
    c.text(2, col, word[0], BOLD)
    c.text(3, col, word[1], BOLD)
    card = f"  {pips(g.results)}  "
    c.text(5, (W - len(card)) // 2, card, REV_BOLD)
    if won:
        twinkle = "♥" if app.t % 2 == 0 else "·"
        c.text(1, 13, twinkle)
        c.text(1, 36, "·" if twinkle == "♥" else "♥")
        c.text(4, 34, twinkle)
        c.text(7, 10, "+20 HAPPY   -10 ENERGY   +1 win")
        line = ("☻", f"{pet.name} does a tiny victory dance.")
    else:
        c.text(7, 8, "+5 HAPPY    -10 ENERGY   fun anyway")
        line = ("☺", f'{pet.name} giggles. "Again? Again!"')
    rule(c)
    status(c, *line)
    footer(c, " p again  ·  any key: back")


def draw_naming(c, app):
    header(c, "new friend", right="hello! ")
    c.sprite(2, 20, app.egg_frame(), BOLD)
    c.text(1, 31, "°")
    c.text(2, 17, "·")
    c.text(4, 32, "·")
    prompt = "A warm egg appeared. What's its name?"
    c.text(7, (W - len(prompt)) // 2, prompt, BOLD)
    c.text(9, 11, "NAME", BOLD)
    cursor = "█" if app.t % 2 == 0 else " "
    c.text(9, 17, f" {app.name_buf}{cursor}".ljust(11), REV)
    c.text(9, 30, "max 8")
    footer(c, " type a name  ·  Enter: done  ·  Bksp: erase")


def draw_stats(c, app):
    pet = app.pet
    stage = pet.stage()
    header(c, pet.name, " · stats", f"{stage.upper()} · {fmt_age(pet.age_seconds())} ")
    for row, (label, stat) in enumerate((("FULL", "fullness"), ("HAPPY", "happy"),
                                         ("ENERGY", "energy"), ("CLEAN", "clean")), start=2):
        v = round(getattr(pet, stat))
        rate = pet.rate_per_hour(stat)
        arrow = "↑" if rate > 0 else "↓" if rate < 0 else "→"
        c.text(row, 1, f"{label:<7}", BOLD if v < 25 else NORMAL)
        c.text(row, 9, f"{pet_art.meter(v, 20)} {v:>3}  {arrow} {abs(rate):.0f}/h")
    c.text(6, 1, "─" * 48)
    born = time.localtime(pet.born)
    hour = time.strftime("%I:%M", born).lstrip("0") + ("a" if born.tm_hour < 12 else "p")
    nxt = pet.next_stage_in()
    upcoming = {"egg": "hatch", "baby": "teen", "teen": "adult"}.get(stage)
    left = [("BORN", f"{time.strftime('%b %d', born)} {hour:>6}"), ("MEALS", pet.meals),
            ("GAMES", f"{pet.wins} / {pet.games} won"), ("NAPS", pet.naps)]
    right = [("MOOD", pet.mood()), ("HUGS", pet.hugs), ("CLEANS", pet.cleans),
             ("NEXT", f"{upcoming} in {fmt_age(nxt)}" if nxt else "all grown up")]
    for row, ((l1, v1), (l2, v2)) in enumerate(zip(left, right), start=7):
        c.text(row, 1, l1, BOLD)
        c.text(row, 8, str(v1))
        c.text(row, 26, l2, BOLD)
        c.text(row, 33, str(v2))
    footer(c, " stats  ·  any key: back  ·  q quit")


def draw_gone(c, app):
    pet = app.pet
    header(c, "empty room", right=f"{fmt_age(pet.age_seconds())} ")
    if app.t < app.gone_since + 3:
        c.text(8, 12, "¶", BOLD)
        rule(c)
        status(c, " ", f"{pet.name}'s room is quiet... there's a note.")
        return
    lines = ["Dear you,", pet_copy.GRANDMA_NOTE[pet.runaway_reason()],
             "went to stay with Grandma. She makes", "the best rice balls. Come visit me! ♥",
             f"{'- ' + pet.name:>38}"]
    c.text(2, 4, "┌" + "─" * 40 + "┐")
    for r in range(3, 8):
        c.text(r, 4, "│" + " " * 40 + "│")
    c.text(8, 4, "└" + "─" * 40 + "┘")
    for r, line in enumerate(lines, start=3):
        c.text(r, 6, line)
    c.text(3, 43, "¶")
    c.text(10, 1, f"{pet.name} stayed {fmt_age(pet.age_seconds())} · {pet.meals} meals · {pet.hugs} hugs")
    footer(c, " n new egg  ·  q quit")
