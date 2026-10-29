"""'Higher or Lower' screens: big cards, mini Mochi reacting, streak panel, history."""

import pet_art
import pet_hilo_art as S
from pet_canvas import BOLD, REV, W
from pet_screens_main import footer, header, rule, status


def big3(text):
    if text == "10":
        return list(S.BIG3_TEN)
    return [" ".join(S.BIG3[ch][r] for ch in text) for r in range(3)]


def _card(c, row, col, card):
    rank, suit = card
    for dy, line in enumerate(S.CARD_FACE):
        c.text(row + dy, col, line.replace("RR", rank.ljust(2)).replace("rr", rank.rjust(2)).replace("S", suit))
    for dy, dx, w in S.CARD_INDEX_CELLS:
        ch = "".join(c.cells[row + dy][col + dx + i][0] for i in range(w))
        c.text(row + dy, col + dx, ch, BOLD)
    big = big3(rank)
    bx = col + (S.CARD_W - len(big[0])) // 2
    for i, dy in enumerate(S.CARD_BIG_ROWS):
        c.sprite(row + dy, bx, [big[i]], BOLD)


def _back(c, row, col):
    for dy, line in enumerate(S.CARD_BACK):
        c.text(row + dy, col, line)
    b = S.CARD_BACK_BIG
    c.sprite(row + b["dy"], col + b["dx"], list(S.BIG3[b["glyph"]]), BOLD)


def _head(c, face, row=S.HEAD_POS[0], col=S.HEAD_POS[1]):
    el, er, m, _ = pet_art.FACES[face]
    rows = [r.replace("E", el, 1).replace("E", er, 1).replace("M", m) for r in S.MOCHI_HEAD]
    c.sprite(row, col, rows, BOLD, S.MOCHI_HEAD_MASK)


def _streak(c, streak, best, new_best):
    c.text(*S.STREAK_LABEL, "STREAK", BOLD)
    big = big3(str(streak)) if streak != 10 else [" ".join(S.BIG3[d][r] for d in "10") for r in range(3)]
    for i, line in enumerate(big):
        c.sprite(S.STREAK_BIG_ROW + i, S.STREAK_BIG_RIGHT + 1 - len(line), [line], BOLD)
    c.text(*S.BEST_LINE, f"best {best:>2}")
    if new_best:
        c.text(*S.BADGE_LINE, " NEW BEST ", REV)


def _history(c, cards):
    c.text(S.HISTORY_ROW, S.HISTORY_COL, "seen", BOLD)
    for i, (r, s) in enumerate(cards[-5:]):
        c.text(S.HISTORY_ROW, 7 + i * S.HISTORY_PITCH, f"{r}{s}")


def draw_hilo(c, app):
    g = app.hilo
    {"intro": _intro, "guess": _guess, "reveal": _reveal, "end": _end}[g.phase](c, app, g)


def _intro(c, app, g):
    name = app.pet.name
    header(c, name, " · play", "HIGHER / LOWER ")
    _back(c, 1, 25)
    _card(c, 1, 13, ("7", "♥"))
    for r, line in enumerate(("Next card:", "higher or", "lower? Go!"), 3):
        c.text(r, 2, line)
    for r, line in enumerate(("A is low", "tie = free", "1 miss: out"), 3):
        c.text(r, 38, line)
    for r, cc, ch in ((1, 4, "♠"), (7, 45, "♦"), (1, 44, "·"), (7, 3, "♣")):
        c.text(r, cc, ch)
    rule(c)
    status(c, "♪", f"{name} shuffles the deck. Shuffle shuffle!")
    c.text(11, 1, "p", REV)
    c.text(11, 3, "start")
    best = app.pet.best_streak
    c.text(11, 34, f"best streak {best:>2}" if best else "first run!")
    footer(c, " play  ·  any key: start  ·  q back")


def _new_best(app, g):
    return g.streak > app.prev_best


def _guess(c, app, g):
    name = app.pet.name
    header(c, name, " · play", "HIGHER / LOWER ")
    _card(c, *S.CUR_CARD, g.current)
    _back(c, *S.NEXT_CARD)
    _head(c, "content")
    c.text(5, 15, "next is..." if app.t % 2 == 0 else "next is.. ")
    c.text(6, 13, "h", REV)
    c.text(6, 15, "▲ higher")
    c.text(7, 13, "l", REV)
    c.text(7, 15, "▼ lower")
    _streak(c, g.streak, max(app.prev_best, g.streak), _new_best(app, g))
    rule(c)
    status(c, "?", f"{name} squints... a {g.current[0]}. Hmm!")
    _history(c, g.history)
    footer(c, " h / ▲ higher  ·  l / ▼ lower  ·  q give up")


def _reveal(c, app, g):
    name, result = app.pet.name, g.result
    header(c, name, " · play", {"right": "√ +1 ", "tie": "free pass ", "wrong": "oh no! "}[result])
    _card(c, *S.CUR_CARD, g.current)
    _card(c, *S.NEXT_CARD, g.next_card)
    _head(c, {"right": "happy", "tie": "tease", "wrong": "sad"}[result])
    arrow = "▲" if g.guess == "higher" else "▼"
    if result == "right":
        c.text(5, 13, " ♪       ♫ ")
        c.text(6, 13, f" {arrow} {g.guess.upper()} ", REV)
        c.text(7, 14, "√ yes! +1", BOLD)
        status(c, "☻", f"{name} hops! {g.streak} in a row. ♪")
    elif result == "tie":
        c.text(6, 14, "=  SAME!", BOLD)
        c.text(7, 14, "free pass")
        status(c, "☺", f"Twins! {name} lets that one slide.")
    else:
        c.text(6, 14, f"{arrow} {g.guess}...", BOLD)
        c.text(7, 14, "x nope!", BOLD)
        status(c, "☺", f"{g.next_card[0]}{g.next_card[1]}? Sneaky card! {name} pouts.")
    _streak(c, g.streak, max(app.prev_best, g.streak), _new_best(app, g))
    rule(c)
    _history(c, g.history)
    footer(c, " any key: next" if result != "wrong" else " any key: see score")


def _end(c, app, g):
    name, res = app.pet.name, app.result
    header(c, name, " · play", f"streak {g.streak} ")
    big = big3(str(g.streak))
    col = (W - len(big[0])) // 2
    for i, line in enumerate(big):
        c.text(2 + i, col, line, BOLD)
    c.text(3, col + len(big[0]) + 2, "in a row!", BOLD)
    _head(c, "love" if res["new_best"] else ("happy" if g.streak >= 5 else "content"), 1, 6)
    if res["new_best"]:
        for r, cc, ch in ((1, 19, "♥"), (1, 33, "·"), (4, 44, "°"), (2, 40, "♥")):
            c.text(r, cc, ch)
        c.text(5, 20, " NEW BEST ", REV)
    else:
        c.text(5, 21, f"best  {app.pet.best_streak}")
    cur, nxt = g.current, g.next_card
    c.text(6, 13, f"last: {cur[0]}{cur[1]} → {nxt[0]}{nxt[1]}, you said {g.guess}")
    line = f"+{res['happy']} HAPPY   {res['energy']} ENERGY   " + ("+1 win" if res["win"] else "fun anyway")
    c.text(7, (W - len(line)) // 2, line)
    rule(c)
    if res["new_best"]:
        status(c, "☻", f"{name} is a card shark now! ♥")
    elif g.streak >= 5:
        status(c, "☻", f"{name} claps its hooves. Nice run! ♪")
    else:
        status(c, "☺", f'{name} giggles. "Again? Again!"')
    footer(c, " p again  ·  any key: back")
