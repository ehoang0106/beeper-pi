"""'Sheep Train' screens: intro, the fenced field with the lamb train, bonk, game over."""

import pet_hilo_art as H
import pet_train_art as S
from pet_canvas import BOLD, REV, W
from pet_screens_main import footer, header, rule, status
from pet_train_game import DIRS


def big3(text):
    return [" ".join(H.BIG3[ch][r] for ch in text) for r in range(3)]


def _pos(gx, gy):
    return S.FIELD_ROW + gy, S.FIELD_COL + 2 * gx


def _cell(c, gx, gy, glyphs, mask="  "):
    r, col = _pos(gx, gy)
    c.sprite(r, col, [glyphs], BOLD, [mask])


def _fence(c):
    c.text(S.FENCE_ROW_TOP, S.FENCE_COL_LEFT, S.FENCE_TOP)
    c.text(S.FENCE_ROW_BOTTOM, S.FENCE_COL_LEFT, S.FENCE_BOTTOM)
    for r in range(S.FENCE_ROW_TOP + 1, S.FENCE_ROW_BOTTOM):
        c.text(r, S.FENCE_COL_LEFT, S.FENCE_SIDE)
        c.text(r, S.FENCE_COL_RIGHT, S.FENCE_SIDE)


def _speed(c, g):
    level = 1 + round((S.STEP_SLOWEST - g.step_seconds()) / 0.15 * 4)
    c.text(*S.SPEED_POS, "speed " + S.SPEED_PIPS[0] * level + S.SPEED_PIPS[1] * (5 - level))


def draw_train(c, app):
    g = app.train
    {"intro": _intro, "playing": _field, "crashed": _field, "end": _end}[g.phase](c, app, g)


def _intro(c, app, g):
    name = app.pet.name
    header(c, name, " · train", "SHEEP TRAIN ")
    _fence(c)
    for row, line, attr in ((3, "Lambs got loose in the field!", BOLD), (4, "Lead them home in a line.", 0)):
        c.text(row, (W - len(line)) // 2, line, attr)
    for i, gx in enumerate(range(8, 2, -1)):  # a little demo train heading right
        if i == 0:
            _cell(c, gx, 6, *S.HEAD["RIGHT"])
        else:
            _cell(c, gx, 6, S.BODY[(gx + 6) % 2])
    _cell(c, 13, 6, *S.LAMB[app.t % 2])
    for r, line in enumerate(("don't bonk the", "fence or the", "train!  ☼"), 7):
        c.text(r, 33, line)
    for i, k in enumerate("wasd"):
        c.text(10, 4 + i * 2, k, REV)
    c.text(10, 12, "or pad: steer")
    c.text(12, 1, "p", REV)
    c.text(12, 3, "start  ·  q back")
    best = app.pet.best_train
    c.text(12, 33, f"best  {best} lambs" if best else "first run!")


def _field(c, app, g):
    name, best = app.pet.name, max(app.pet.best_train, g.score)
    crashed = g.phase == "crashed"
    eating = g.frame - g.eat_frame < S.EAT_FLASH_STEPS and not crashed
    hud = "BONK! " if crashed else (S.EAT_HUD if eating else S.HUD).format(score=g.score, best=best)
    header(c, name, " · train", hud)
    _fence(c)
    footer(c, S.FOOTER)
    _speed(c, g)
    if g.lamb:
        _cell(c, *g.lamb, *S.LAMB[app.t % 2])
    cells = list(g.train)
    for gx, gy in cells[1:]:
        _cell(c, gx, gy, S.BODY[(gx + gy) % 2])
    hx, hy = cells[0]
    _cell(c, hx, hy, *(S.HEAD_BONK if crashed else S.HEAD[g.facing]))
    if eating and hy > 0 and (hx, hy - 1) not in g.train:
        r, col = _pos(hx, hy)
        c.text(r + S.EAT_NOTE[0], col, S.EAT_NOTE[2], BOLD)
    if crashed:
        _bonk(c, g, hx, hy)


def _bonk(c, g, hx, hy):
    """Twinkling impact where the head hit, plus a BONK! bubble if it fits."""
    star = S.IMPACT[g.frame % 2]
    dx, dy = DIRS[g.facing]
    tx, ty = hx + dx, hy + dy
    r, col = _pos(hx, hy)
    if not 0 <= tx < g.w:  # side fence
        c.text(r, S.FENCE_COL_LEFT if tx < 0 else S.FENCE_COL_RIGHT, star, BOLD)
    elif not 0 <= ty < g.h:  # top / bottom fence
        c.text(S.FENCE_ROW_TOP if ty < 0 else S.FENCE_ROW_BOTTOM, col, star * 2, BOLD)
    else:  # its own train: mark the first char of the lamb it hit
        tr, tc = _pos(tx, ty)
        c.text(tr, tc, star, BOLD)
    bubble = S.BONK_BUBBLE
    bc = max(S.FIELD_COL, min(S.FIELD_COL + 2 * S.GRID_W - len(bubble), col + 1 - len(bubble) // 2))
    for br in (r - 1, r + 1):
        if S.FIELD_ROW <= br < S.FIELD_ROW + S.GRID_H and all(
                c.cells[br][bc + i][0] == " " for i in range(len(bubble))):
            c.text(br, bc, bubble, REV)
            return


def _end(c, app, g):
    name, res = app.pet.name, app.result
    header(c, name, " · train", f"{g.score} lambs ")
    big = big3(str(g.score))
    col = (W - len(big[0])) // 2
    for i, line in enumerate(big):
        c.text(2 + i, col, line, BOLD)
    lx = col + len(big[0]) + 2
    c.text(2, lx, "lambs", BOLD)
    c.text(3, lx, "led home")
    if res["new_best"]:
        c.text(4, lx, " NEW BEST ", REV)
        for r, cc, ch in ((2, 14, "♥"), (1, 33, "·"), (1, 44, "°"), (4, 10, "°")):
            c.text(r, cc, ch)
    else:
        c.text(4, lx, f"best {app.pet.best_train}")
    n = min(g.score, S.PARADE_MAX)
    more = f" +{g.score - n}" if g.score > n else ""
    x0 = (W - (n * S.PARADE_PITCH - 1 + len(more))) // 2
    for i in range(n):
        c.sprite(S.PARADE_ROW, x0 + i * S.PARADE_PITCH, [S.LAMB[0][0]], BOLD, [S.LAMB[0][1]])
    if more:
        c.text(S.PARADE_ROW, x0 + n * S.PARADE_PITCH - 1, more)
    line = f"+{res['happy']} HAPPY   {res['energy']} ENERGY   " + ("+1 win" if res["win"] else "fun anyway")
    c.text(8, (W - len(line)) // 2, line)
    rule(c)
    if res["new_best"]:
        status(c, "☻", f"Choo choo! {name} is the best shepherd! ♥")
    elif g.score >= 10:
        status(c, "☻", f"{name} counts the lambs proudly. ♪")
    else:
        status(c, "☺", f"{name} rubs its head. Ouch! Again?")
    footer(c, " p again  ·  any key: back")
