"""Sheep Train (snake): field, fence, cell glyphs and tuning (pure data, no imports).

Conventions match pet_art: mask "R" cells are drawn inverted against what's under
them (the field is light, so R = a dark cell with a light glyph). Blit a 2-char
cell with Canvas.sprite(row, col, [glyphs], BOLD, [mask]). Beepy-font glyphs only.

Grid: cells are 2 chars wide x 1 row tall (16x16 px, square).
  cell (gx, gy) -> canvas (row, col) = (FIELD_ROW + gy, FIELD_COL + 2 * gx)
  gx 0..GRID_W-1, gy 0..GRID_H-1  -> TrainGame(GRID_W, GRID_H)
"""

# ---------------------------------------------------------------- field
GRID_W, GRID_H = 23, 9        # 207 cells
FIELD_ROW, FIELD_COL = 2, 2   # top-left cell of the playfield (inside the fence)
# Fence occupies rows 1 and 11, cols 1 and 48 (playfield rows 2-10, cols 2-47).
# Row 0 = header/HUD, row 12 = footer. Cols 0 and 49 stay blank.
FENCE_ROW_TOP, FENCE_ROW_BOTTOM = 1, 11
FENCE_COL_LEFT, FENCE_COL_RIGHT = 1, 48

# Double-rail sheep pen: rails "═", posts "╦"/"╩" every 5 cols. Draw NORMAL.
# Each string starts at FENCE_COL_LEFT and is 48 chars wide.
FENCE_TOP = "╔════╦════╦════╦════╦════╦════╦════╦════╦════╦═╗"
FENCE_BOTTOM = "╚════╩════╩════╩════╩════╩════╩════╩════╩════╩═╝"
FENCE_SIDE = "║"  # rows 2-10 at cols 1 and 48

# ---------------------------------------------------------------- the train
# Mochi's head: a solid dark square (both cells masked R) with the eye(s) on the
# side it faces. Up = eyes high (°), down = eyes low (.).
HEAD = {
    "RIGHT": (" °", "RR"),
    "LEFT": ("° ", "RR"),
    "UP": ("°°", "RR"),
    "DOWN": ("..", "RR"),
}
HEAD_BONK = ("xx", "RR")  # crash frames

# Lambs in the train: wool squares that alternate by GRID PARITY, not by index,
# so a cell keeps its glyph while the train moves through it and only the head,
# neck and tail cells change each step (memory-LCD friendly). Adjacent cells
# always differ in parity, so lambs read as separate "cars".
#   glyph = BODY[(gx + gy) % 2], drawn BOLD, no mask
BODY = {0: "▒▒", 1: "▓▓"}

# The loose lamb to collect: wool + a little dark face that looks left/right.
# Swap frames every 500 ms (2 cells change). Drawn BOLD with the mask.
LAMB = [("▒°", " R"), ("°▒", "R ")]

# ---------------------------------------------------------------- feedback
# Eat: for EAT_FLASH_STEPS steps the header's right side reads EAT_HUD (bold
# feel comes from the copy; header stays REV) and a note pops one cell above the
# head if that cell is empty field: (dy, dx, glyph) relative to the head cell.
EAT_FLASH_STEPS = 2
EAT_HUD = " baa! ♥ {score} lambs  best {best} "
EAT_NOTE = (-1, 0, "♪")          # skip if off-field or occupied

# Crash ("bonk"), CRASH_FRAMES = 4 steps in pet_train_game:
#  - head -> HEAD_BONK (x eyes)
#  - impact cell: if the head ran into the fence, the fence char(s) in front of
#    the head become IMPACT (top/bottom fence: both chars at col, col+1 of the
#    head cell; side fence: the one "║"). If it hit its own train, draw IMPACT
#    over the FIRST char of the lamb it hit (keep the 2nd wool char).
#  - BONK_BUBBLE drawn REV on the row above the head, else the row below, only
#    if all its cells are empty field (it must never hide the train); otherwise
#    the header's "BONK!" carries the moment alone. Centered on the head,
#    clamped to playfield cols 2..47.
#  - header right: "BONK! "
#  Frames alternate the impact glyph IMPACT[frame % 2] so the star twinkles.
IMPACT = ["☼", "*"]
BONK_BUBBLE = " BONK! "

# ---------------------------------------------------------------- HUD / footer
HUD = " ♥ {score} lambs  best {best} "            # header right while playing
FOOTER = " w a s d / pad: steer  ·  q give up"
SPEED_POS = (12, 39)                    # "speed" + 5 pips, e.g. "speed ►►►··"
SPEED_PIPS = ("►", "·")

# Speed level 1..5 = 1 + round((0.30 - step) / 0.15 * 4)

# ---------------------------------------------------------------- tuning
# Matches pet_train_game: step = max(0.15, 0.30 - 0.01 * score)
#   score 0 -> 0.30 s | 5 -> 0.25 | 10 -> 0.20 | 15+ -> 0.15 (cap)
STEP_SLOWEST, STEP_FASTEST, STEP_PER_LAMB = 0.30, 0.15, 0.01
START_LEN = 3            # Mochi + 2 lambs, at (GRID_W // 4, GRID_H // 2) facing right
# Rewards by lambs collected: (min_score, happy, energy, counts_as_win)
REWARDS = [(20, 20, -10, True), (10, 15, -10, True), (4, 10, -10, False), (0, 5, -10, False)]
NEW_BEST_BONUS_HAPPY = 5

# ---------------------------------------------------------------- game-over parade
# Big score rows 2-4 centered; "lambs"/"led home"/badge-or-"best N" on rows 2-4
# right of the digits (+2 cols). Up to PARADE_MAX mini lambs on row PARADE_ROW (one per lamb collected, then
# "+N"), pitch 3, centered. Each icon is the LAMB frame 0 glyph pair.
PARADE_ROW = 6
PARADE_MAX = 12
PARADE_PITCH = 3
