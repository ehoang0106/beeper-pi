"""Higher or Lower: card templates, big rank font, mini Mochi head, layout (pure data).

Conventions match pet_art: spaces in sprites are transparent; mask "R" cells are
drawn inverted against what's under them. Glyphs are all in the Beepy font.
Coordinates are (row, col) on the 50x13 canvas.
"""

# ---------------------------------------------------------------- big font (3x3)
# Half-block 7-segment style: 3 cols x 3 rows = 3x6 "pixels". Draw BOLD.
# Used for the card's center rank, the streak counter, and (shared) the Sheep
# Train score. Suggest merging into pet_art as BIG3 with a big3_text() helper:
#   rows[r] = " ".join(BIG3[ch][r] for ch in text)   (1-col gap between glyphs)
# "10" is special: it uses the narrow "1" (BIG3_TEN), so it is 6 cols wide.
BIG3 = {
    "0": ("█▀█", "█ █", "█▄█"),
    "1": ("▀█ ", " █ ", "▄█▄"),
    "2": ("▀▀█", "█▀▀", "█▄▄"),
    "3": ("▀▀█", " ▀█", "▄▄█"),
    "4": ("█ █", "▀▀█", "  █"),
    "5": ("█▀▀", "▀▀█", "▄▄█"),
    "6": ("█▀▀", "█▀█", "█▄█"),
    "7": ("▀▀█", "  █", "  █"),
    "8": ("█▀█", "█▀█", "█▄█"),
    "9": ("█▀█", "▀▀█", "▄▄█"),
    "A": ("█▀█", "█▀█", "█ █"),
    "J": (" ▀█", "  █", "▀▄▀"),
    "Q": ("█▀█", "█ █", "▀█▄"),
    "K": ("█ █", "██ ", "█ █"),
    "?": ("▀▀█", " █▀", " ▄ "),
}
BIG3_TEN = ("▀█ █▀█", " █ █ █", "▄█ █▄█")  # rank "10": narrow 1 + gap + 0

# ---------------------------------------------------------------- cards (11x8)
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]  # A low
SUITS = ["♥", "♦", "♣", "♠"]
CARD_W, CARD_H = 11, 8

# Face template. Substitution rules (plain str.replace, then draw):
#   "RR" -> rank.ljust(2)   top-left index  ("A ", "10")
#   "rr" -> rank.rjust(2)   bottom-right index (" A", "10")
#   "S"  -> suit            (both corners; replace all)
# Draw the frame NORMAL, then re-draw the two corner index cells BOLD
# (CARD_INDEX_CELLS), then overlay the big rank BOLD on rows CARD_BIG_ROWS,
# horizontally centered: col = card_col + (CARD_W - big_width) // 2
# (3-wide glyph -> dx 4; "10" (6 wide) -> dx 2). The big rank never touches
# the corner indices.
CARD_FACE = [
    "┌─────────┐",
    "│RR       │",
    "│S        │",
    "│         │",
    "│         │",
    "│        S│",
    "│       rr│",
    "└─────────┘",
]
CARD_BIG_ROWS = (3, 4, 5)                  # dy inside the card
CARD_INDEX_CELLS = [(1, 1, 2), (2, 1, 1), (5, 9, 1), (6, 8, 2)]  # (dy, dx, width) BOLD

# Face-down card: woolly ▒ back with a big "?" window. Draw NORMAL, then the
# "?" cells (CARD_BACK_BIG at dy 3..5, dx 4) BOLD.
CARD_BACK = [
    "┌─────────┐",
    "│▒▒▒▒▒▒▒▒▒│",
    "│▒▒     ▒▒│",
    "│▒▒     ▒▒│",
    "│▒▒     ▒▒│",
    "│▒▒     ▒▒│",
    "│▒▒▒▒▒▒▒▒▒│",
    "└─────────┘",
]
CARD_BACK_BIG = {"dy": 3, "dx": 4, "glyph": "?"}

# Optional flip: ONE in-between frame (~150 ms) when the hidden card turns over.
# Clear the 11x8 box, draw CARD_EDGE centered (dx 4), then the face. If the 500 ms
# tick can't do sub-frames, skip it (face appears directly; still reads fine).
CARD_EDGE = ["┌─┐", "│▒│", "│▒│", "│▒│", "│▒│", "│▒│", "│▒│", "└─┘"]

# ---------------------------------------------------------------- mini Mochi (9x4)
# Shaun-style head that reacts between the cards: grey wool cap (▒), dark face
# made of mask-"R" cells (eyes/mouth become light glyphs on the dark face), ears ▀.
# Template letters as pet_art: E = eye (left, then right), M = mouth; faces come
# from pet_art.FACES (eye/mouth glyphs only; cheek is ignored).
MOCHI_HEAD = [
    " ▄▒▒▒▒▒▄ ",
    "▀█ E E █▀",
    "  █ M █  ",
    "   ▀▀▀   ",
]
MOCHI_HEAD_MASK = [
    "         ",
    "  RRRRR  ",
    "   RRR   ",
    "         ",
]
# face per moment (keys of pet_art.FACES)
MOCHI_FACE = {
    "intro": "happy", "guess": "content", "guess_blink": "sleepy_b",
    "right": "happy", "tie": "tease", "wrong": "sad", "end_best": "love",
    "end": "content", "end_zero": "sad",
}
# Thinking dots above the head while guessing: cycle one cell per tick.
# "next is..." under the head (row 5, col 15): the trailing dot blinks each tick.

# ---------------------------------------------------------------- layout
CUR_CARD = (1, 1)      # current (face-up) card top-left
NEXT_CARD = (1, 26)    # next (face-down / revealed) card top-left
HEAD_POS = (1, 14)     # mini Mochi top-left (cols 14-22, rows 1-4)
# Middle prompt block (cols 13-24), rows 6-7 during a guess:
PROMPT_HI = (6, 13)    # "h" keycap REV at col 13, then " ▲ higher" from col 14
PROMPT_LO = (7, 13)    # "l" keycap REV, then " ▼ lower"
# Streak panel (cols 38-48)
STREAK_LABEL = (1, 39)     # "STREAK" BOLD
STREAK_BIG_ROW = 2         # rows 2-4, right-aligned to col 47
STREAK_BIG_RIGHT = 47
BEST_LINE = (6, 39)        # "best  9"
BADGE_LINE = (7, 39)       # " NEW BEST " REV, only once streak > previous best
HISTORY_ROW = 11           # "seen  A♥  5♣  10♦ ..." oldest -> newest, max 5
HISTORY_COL = 1
HISTORY_PITCH = 4          # each card text left-justified in 4 cols

# Result line in the middle block during a reveal (rows 6-7), cols 13-24:
RESULT_MARK = {"right": "√", "tie": "=", "wrong": "x"}

# ---------------------------------------------------------------- tuning
REVEAL_SECONDS = 1.5          # matches REVEAL_FRAMES = 3 at 500 ms; any key skips
# Rewards by final streak: (min_streak, happy, energy, counts_as_win)
REWARDS = [(10, 20, -5, True), (5, 15, -5, True), (2, 10, -5, False), (0, 5, -5, False)]
NEW_BEST_BONUS_HAPPY = 5
