"""3-game menu: card positions, art and copy (pure data, no imports).

Three 14x7 cards on rows 2-8 at cols 1, 18, 35 (1-col screen margins, 3-col gaps).
Card frame: "┌" + "─"*12 + "┐", "│" + " "*12 + "│" x5, "└" + "─"*12 + "┘", NORMAL.
Keycap " n " REV on the top border at col+2. Art at (row 3, col + ART_DX[i]),
BOLD with its mask (R = inverted cell). Title row 6 BOLD at col+1 (inner width 12),
subtitle row 7 at col+1. Info line row 9 under each card (col+1), best scores
filled in at runtime ("{best}" placeholder; show "new!" when never played).
"""

CARD_W, CARD_H = 14, 7
CARD_ROW = 2
CARD_COLS = [1, 18, 35]
KEYS = ["1", "2", "3"]
TITLES = ["Which paw?", "Sheep Train", "Higher/Lower"]
SUBTITLES = ["find the ▲", "lead lambs", "guess cards"]
INFO = ["5 rounds", "best {best}", "best {best}"]
INFO_NEVER = "new!"           # replaces "best {best}" until the first run

# Art: 3 rows each, drawn at row 3. ART_DX = col offset inside the card.
ART = [
    ["┌─┐ ┌─┐", "│▲│ │?│", "└─┘ └─┘"],
    ["            ", "▒▓▒▓▒▓ °  ▒°", "╩═══╩════╩══"],
    ["┌──┐▲┌──┐", "│K♠│ │▒▒│", "└──┘▼└──┘"],
]
ART_MASK = [
    None,
    ["            ", "      RR   R", "            "],
    None,
]
ART_DX = [3, 1, 2]

# Train art: wool cars ▒▓, Mochi's head = 2 masked cells " °" (dark, eye right),
# a gap, then a loose lamb "▒°" with its face masked. Row 0 blank, row 2 = the pen rail.

HEADER_RIGHT = "pick a game "
PROMPT = "What shall we play?"            # row 1, col 2, BOLD
STATUS = ("♪", "{name} wants to play! Pick one.")   # row 10
FOOTER = " 1 2 3 pick  ·  q back"         # row 12
