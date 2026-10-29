"""The 3-game menu: Which paw? · Sheep Train · Higher or Lower."""

import pet_menu_art as M
from pet_canvas import BOLD, REV
from pet_screens_main import footer, header, status

BEST_FIELDS = [None, "best_train", "best_streak"]  # per card; None = no best score


def draw_menu(c, app):
    pet = app.pet
    header(c, pet.name, " · play", M.HEADER_RIGHT)
    c.text(1, 2, M.PROMPT, BOLD)
    inner = M.CARD_W - 2
    for i, col in enumerate(M.CARD_COLS):
        c.text(M.CARD_ROW, col, "┌" + "─" * inner + "┐")
        for r in range(M.CARD_ROW + 1, M.CARD_ROW + M.CARD_H - 1):
            c.text(r, col, "│" + " " * inner + "│")
        c.text(M.CARD_ROW + M.CARD_H - 1, col, "└" + "─" * inner + "┘")
        c.text(M.CARD_ROW, col + 2, f" {M.KEYS[i]} ", REV)
        c.sprite(3, col + M.ART_DX[i], M.ART[i], BOLD, M.ART_MASK[i])
        c.text(6, col + 1, M.TITLES[i], BOLD)
        c.text(7, col + 1, M.SUBTITLES[i])
        best = getattr(pet, BEST_FIELDS[i]) if BEST_FIELDS[i] else None
        info = M.INFO[i] if "{best}" not in M.INFO[i] else (
            M.INFO[i].format(best=best) if best else M.INFO_NEVER)
        c.text(9, col + 1, info)
    glyph, text = M.STATUS
    status(c, glyph, text.format(name=pet.name))
    footer(c, M.FOOTER)
