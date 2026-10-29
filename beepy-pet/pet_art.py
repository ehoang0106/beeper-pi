"""Beepy pet artwork: sprite templates, faces, egg frames, big text and meters.

Only CP437 glyphs the Beepy console font can draw are used. Sprites are templates:
E = eye (first E is the left eye, second the right), M = mouth, b = cheek slot.
Spaces are transparent when blitted, so particles can pass behind the outline.
"""

# Sheep sprites in the spirit of Shaun the Sheep (fan art), drawn from the user's
# references: the baby follows a bead-art lamb (square head, white goggle eyes, round
# wool body, grey arms); the adult has Shaun's wool cap, droopy ears and long face.
# Fixed box per stage so nothing jumps when the face changes.
TEMPLATES = {
    "baby": [
        "▄▄█▀▀▀█▀▀▀█▄▄",
        "▀ █ E █ E █ ▀",
        "  █▄▄▄█▄▄▄█  ",
        " ▄▐b∙ M ∙b▌▄ ",
        "▒▌         ▐▒",
        " ▀▄▄█▀▀▀█▄▄▀ ",
    ],
    "teen": [
        "    ▄▀▀▀▀▀▄    ",
        "▄▄▄██▀███▀██▄▄▄",
        "▀  █ E █ E █  ▀",
        "▄▀ ██▄███▄██ ▀▄",
        "▀▄ ▀█b███b█▀ ▄▀",
        "█   █∙█M█∙█   █",
        " ▀██  ▀▀▀  ██▀ ",
    ],
    "adult": [
        "    ▄▄▀▀▀▀▀▀▀▄▄    ",
        "   █ ▄ ▄ ▄ ▄ ▄ █   ",
        " ▄▄▄███▀███▀███▄▄▄ ",
        "█▀▀▀▀█ E █ E █▀▀▀▀█",
        " ▄▀  ██▄███▄██  ▀▄ ",
        "▀▄   ██b███b██   ▄▀",
        "  ▀██ █∙█M█∙█ ██▀  ",
    ],
}

# R marks cells drawn inverted against what's under them (light glyph on the dark
# face by day, flipped at night) even where the template is blank.
MASKS = {
    "baby": [
        "             ",
        "             ",
        "             ",
        "   RRRRRRR   ",
        "             ",
        "             ",
    ],
    "teen": [
        "               ",
        "               ",
        "               ",
        "               ",
        "     R   R     ",
        "     R R R     ",
        "               ",
    ],
    "adult": [
        "                   ",
        "                   ",
        "                   ",
        "                   ",
        "                   ",
        "       R   R       ",
        "       R R R       ",
    ],
}

# face -> (left eye, right eye, mouth, cheek)
FACES = {
    "content": ('■', '■', '─', ' '),
    "happy": ('^', '^', '▼', ' '),
    "hungry": ('■', '■', 'o', ' '),
    "eat_a": ('^', '^', 'O', ' '),
    "eat_b": ('^', '^', '▬', ' '),
    "sad": ('╥', '╥', '∩', ' '),
    "sad_tear": ('╥', '╥', '∩', '°'),
    "sleepy": ('▬', '▬', 'o', ' '),
    "sleepy_b": ('▬', '▬', '─', ' '),
    "sleeping": ('─', '─', '·', ' '),
    "snore": ('─', '─', 'o', ' '),
    "dirty": ('■', '■', '~', '░'),
    "sick": ('x', 'x', '~', ' '),
    "love": ('♥', '♥', '▼', ' '),
    "tease": ('^', '■', 'p', ' '),
    "refuse": ('>', '<', '-', ' '),
}

# A woolly egg: same scalloped fringe as the adult's wool cap.
EGG = [
    "  ▄▀▄▀▄▀▄  ",
    " █       █ ",
    "▐  ° ∙ °  ▌",
    " █  ∙ °  █ ",
    "  ▀▄▄▄▄▄▀  ",
]

# Hatching frames, bottom-aligned with the egg. The last one lifts the wool lid
# a row and the baby's goggle eyes peek out of the shell.
HATCH = [
    EGG,
    ["  ▄▀▄▀▄▀▄  ", " █       █ ", "▐  °/\\/°  ▌", " █  ∙ °  █ ", "  ▀▄▄▄▄▄▀  "],
    ["  ▄▀▄▀▄▀▄  ", " █   /   █ ", "▐ °/\\/\\/° ▌", " █  ∙ °  █ ", "  ▀▄▄▄▄▄▀  "],
    ["  ▄▀▄▀▄▀▄  ", " █▄▄▄▄▄▄▄█ ", "▐ █■█ █■█ ▌", " █\\/\\/\\/\\█ ", " █  ∙ °  █ ", "  ▀▄▄▄▄▄▀  "],
]

# Where each stage stands: (x, y) of the sprite's top-left cell on the 50x13 canvas.
# Centered on column 12 with feet on row 8, just above the floor rule.
def sprite_pos(stage):
    rows = EGG if stage == "egg" else TEMPLATES[stage]
    w, h = len(rows[0]), len(rows)
    return 12 - w // 2, 9 - h


def sprite(stage, face, blink=False):
    """Render a stage template with a face from FACES; blink closes the eyes only."""
    if stage == "egg":
        return EGG
    eye_l, eye_r, mouth, cheek = FACES[face]
    if blink:
        eye_l = eye_r = "-"
    out = []
    for row in TEMPLATES[stage]:
        if "E" in row:
            row = row.replace("E", eye_l, 1).replace("E", eye_r, 1)
        out.append(row.replace("M", mouth).replace("b", cheek))
    return out


def mouth_cell(stage):
    """(dx, dy) of the mouth inside the sprite box, for anchoring food particles."""
    for dy, row in enumerate(TEMPLATES[stage]):
        if "M" in row:
            return row.index("M"), dy
    raise ValueError(stage)


def egg_lean(direction):
    """Wobble frame: the top half of the egg leans left (-1) or right (+1)."""
    if direction == 0:
        return EGG
    top = [r[1:] + " " if direction < 0 else " " + r[:-1] for r in EGG[:2]]
    return top + EGG[2:]


# Action animations, one entry per 500 ms tick: (face, [(dy, dx, glyph), ...]).
# Particle offsets are relative to the sprite's top-left cell and were measured on
# the adult; they read fine on smaller stages too because they stay near the head.
EFFECTS = {
    "feed": [
        ("hungry", [(-2, 11, "▲")]),
        ("hungry", [(1, 13, "▲")]),
        ("eat_a", []),  # food sits beside the mouth: added in the screen code
        ("eat_b", [(3, 5, "·"), (3, 8, "·")]),
        ("happy", [(-2, 11, "nom!")]),
    ],
    "hug": [
        ("happy", [(-1, 5, "♥")]),
        ("love", [(-2, 4, "♥"), (-1, 8, "♥")]),
        ("love", [(-2, 8, "♥"), (-1, 1, "♥"), (-2, -1, "·")]),
        ("content", [(-2, 1, "·"), (-2, 12, "·")]),
    ],
    "clean": [
        ("snore", [(1, -1, "°"), (3, -3, "o"), (4, 14, "O")]),
        ("snore", [(0, -1, "·"), (1, -3, "°"), (2, 14, "o"), (3, 13, "O")]),
        ("happy", [(0, -3, "·"), (0, 14, "°"), (1, 13, "o")]),
        ("happy", [(-2, -2, "·"), (-1, 11, "√")]),
    ],
    "wake": [
        ("happy", [(-1, 11, "☼")]),
        ("happy", [(-1, 11, "☼")]),
    ],
    "refuse": [("refuse", []), ("refuse", [])],
    "love": [("love", [(-1, 5, "♥")]), ("love", [(-2, 5, "♥")])],
}

# 3x2 half-block letters for the YAY! / OOPS screens (same family as the home clock).
BIG_FONT = {
    "Y": ("█ █", " █ "),
    "A": ("▄▀▄", "█▀█"),
    "!": ("█", "▄"),
    "O": ("█▀█", "█▄█"),
    "P": ("█▀█", "█▀▀"),
    "S": ("▄▀▀", "▄▄▀"),
}


def big_text(word):
    """Two rows of big half-block text, letters separated by one column."""
    return [" ".join(BIG_FONT[c][r] for c in word) for r in (0, 1)]


def meter(value, cells):
    """`▓▓▓░░░▌` meter matching the home screen's battery bar."""
    filled = round(max(0, min(100, value)) * cells / 100)
    return "▓" * filled + "░" * (cells - filled) + "▌"
