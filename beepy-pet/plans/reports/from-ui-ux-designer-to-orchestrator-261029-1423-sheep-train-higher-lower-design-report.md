# Design: Sheep Train + Higher or Lower + 3-game menu

Date 2026-10-29 · designer → orchestrator · all previews rendered in the real Beepy 8x16 font.

## Deliverables (all in /tmp/claude-1000/sheep/)
| What | File |
|---|---|
| Train data | `train_sprites.py` |
| Hi/Lo data (incl. shared BIG3 font) | `hilo_sprites.py` |
| Menu data | `menu3_data.py` |
| Reference draw code | `train_mock.py`, `hilo_mock.py`, `menu3_mock.py` |
| Show the user | `menu3.png`, `train_all.png`, `hilo_all.png` (+ per-screen `train_*.png`, `hilo_*.png`) |

Ignore `train_try*/train_v*/train_h*/hilo_try*/*_check*.png` (scratch).

Data files: no imports, functions or computed values (literal strings only). Aligned to the existing `pet_train_game.py` / `pet_hilo_game.py` (phases, START_LEN, speed constants, history of 5, result right/tie/wrong).

---

## 1. Sheep Train (snake)

### Grid
- `TrainGame(23, 9)`. Cell (gx, gy) → `(row, col) = (2 + gy, 2 + 2*gx)`; each cell is 2 chars (16x16 px square).
- The fence is a double-rail pen: rows 1 and 11, cols 1 and 48, with `╦`/`╩` posts every 5 cols. Literal `FENCE_TOP`/`FENCE_BOTTOM` strings start at col 1. The playfield is rows 2-10, cols 2-47.
- Row 0 = header/HUD (`♥ 7 lambs  best 23`). Row 12 = footer with the key hints, plus `speed ►►►··` at col 39.
- With the current logic, the train starts at (5,4) facing right.

### Cell glyphs
- **Head:** a solid dark square (both cells mask R) with the eye on the side it faces:
  - RIGHT `" °"`, LEFT `"° "`, UP `"°°"` (eyes high), DOWN `".."` (eyes low).
  - Crash head: `"xx"`.
- **Lambs:** `▒▒` / `▓▓`, chosen by **grid parity** `(gx+gy)%2`, not by index. Adjacent cells always alternate, so the train reads as separate "cars". A cell also keeps its glyph while the train passes through it, so each step only changes the head, neck and tail cells (good for the memory LCD).
  - I dropped the "walking wiggle" idea: it would redraw the whole train every step.
- **Loose lamb:** `▒°` ↔ `°▒` (face masked R), swapped every 500 ms, so it "looks around". It is the only half-dark cell on the field, so it is easy to spot.

### Moments
- **Eat:** for 2 steps the header reads `baa! ♥ 8 lambs  best 23`, and a `♪` pops one cell above the head if that cell is free field.
- **Crash (4 frames):**
  - The head becomes `xx` and the header right reads `BONK!`.
  - The impact cell twinkles `☼`/`*`:
    - Fence hit: replaces the rail char(s) in front of the head.
    - Self hit: replaces the 1st char of the lamb that was hit.
  - A ` BONK! ` REV bubble goes on the row above the head, else the row below. Draw it **only if every cell it covers is empty field**; otherwise the header carries the moment alone. The rule is implemented in `train_mock.bubble()`.
- **Intro:** the same pen, so starting feels instant. It has the copy, a demo train and lamb, `w a s d` keycaps, and `p start · q back · best 23 lambs` on row 12.
- **Game over:**
  - Big BIG3 score on rows 2-4, with `lambs` / `led home` / ` NEW BEST ` REV (or `best N`) to its right.
  - Row 6: a lamb parade, one icon per lamb, max 12 then `+N`.
  - Row 8: rewards. Then the usual rule, status and footer (`p again · any key: back`).

### Speed curve (matches the code)
`step = max(0.15, 0.30 - 0.01*score)`: score 0 → 0.30 s, 5 → 0.25 s, 10 → 0.20 s, 15+ → 0.15 s.

Speed pips = `1 + round((0.30-step)/0.15*4)` (1..5). Suggestion: keep the input queue at 2 turns, since 0.15 s needs it.

### Rewards (lambs) — suggestion
| lambs | HAPPY | ENERGY | win |
|---|---|---|---|
| 0-3 | +5 | -10 | no |
| 4-9 | +10 | -10 | no |
| 10-19 | +15 | -10 | yes |
| 20+ | +20 | -10 | yes |

NEW BEST adds +5 HAPPY. Energy is -10 because it is an active game, the same as Which paw.

### Copy
| State | Copy |
|---|---|
| intro | "Lambs got loose in the field!" / "Lead them home in a line." / "don't bonk the / fence or the / train! ☼" / "or pad: steer" |
| footer | " w a s d / pad: steer  ·  q give up" |
| end (NEW BEST) | "☻ Choo choo! {name} is the best shepherd! ♥" |
| end (≥10) | "☻ {name} counts the lambs proudly. ♪" |
| end (other) | "☺ {name} rubs its head. Ouch! Again?" |

All lines are ≤ 46 cols with an 8-char name (checked: max is 44).

---

## 2. Higher or Lower

### Layout (guess screen)
| Cols | Content |
|---|---|
| 1-11 | Current card (11x8, rows 1-8) |
| 14-22 | Mini Mochi head (rows 1-4). Row 5 `next is...` (the dot blinks). Rows 6-7: `h` ▲ higher / `l` ▼ lower keycaps |
| 26-36 | Next card, face down |
| 38-48 | `STREAK` + big BIG3 number (right-aligned to col 47), `best  9`, ` NEW BEST ` REV once beaten |

- Row 9: rule. Row 10: Mochi's line.
- Row 11: `seen  2♥  K♠  5♦  J♣`, oldest to newest, pitch 4, max 5.
- Row 12: keys.

### Card template (11x8): `CARD_FACE`
- Substitute `RR` → `rank.ljust(2)`, `rr` → `rank.rjust(2)`, `S` → suit (all).
- Draw the frame NORMAL, then re-draw `CARD_INDEX_CELLS` BOLD.
- Overlay the big rank BOLD on rows dy 3-5, at col `card_col + (11 - w)//2`.
  - `BIG3[rank]` is 3 wide. `"10"` uses `BIG3_TEN` (6 wide, narrow 1).
- **Back:** `CARD_BACK` (▒ wool frame) + big `?` (BIG3 `"?"`) BOLD at dy 3, dx 4.
- **Optional flip:** one `CARD_EDGE` frame (~150 ms). Skip it if the 500 ms tick can't do sub-frames.

### BIG3 font (3x3 half-block, 7-segment style)
- Covers 0-9, A, J, Q, K, ?.
- Used for the card rank, the streak and the Train score.
- I recommend moving it into `pet_art` (e.g. `BIG3` + a `big3_text()` with a 1-col gap) so both games share it. For now `train_mock` imports it from `hilo_sprites`.

### Mini Mochi head (9x4): `MOCHI_HEAD`
- Wool cap `▒`, dark face built from mask-R cells, ears `▀`. Eye and mouth come from `pet_art.FACES`, so it reuses existing faces.
- Face map is in `MOCHI_FACE`:

| Moment | Face |
|---|---|
| guess | content |
| right | happy |
| tie | tease |
| wrong | sad |
| end with new best | love |

### Moments
- **reveal-right:**
  - The card turns face up.
  - Middle: `♪ ♫` on row 5, a REV ` ▲ HIGHER ` chip and `√ yes! +1`.
  - The streak digit ticks up, and the header right shows `√ +1`.
- **tie:** `=  SAME!` / `free pass`, header `free pass`. The streak is unchanged.
- **wrong:** `▲ higher...` / `x nope!`, sad face, header `oh no!`, footer `any key: see score`.
- **end:**
  - Mini head (left), big streak centered, `in a row!`.
  - ` NEW BEST ` or `best N`.
  - `last: 10♦ → A♠, you said higher`.
  - Rewards, status, `p again · any key: back`.

### Rewards (streak) — suggestion
| streak | HAPPY | ENERGY | win |
|---|---|---|---|
| 0-1 | +5 | -5 | no |
| 2-4 | +10 | -5 | no |
| 5-9 | +15 | -5 | yes |
| 10+ | +20 | -5 | yes |

NEW BEST adds +5 HAPPY. Energy is only -5 because it is a calm game.

### Copy
| State | Copy |
|---|---|
| intro | "Next card: / higher or / lower? Go!" · "A is low / tie = free / 1 miss: out" · "♪ {name} shuffles the deck. Shuffle shuffle!" · row 11 `p start` + `best streak  9` |
| guess | "? {name} squints... a {rank}. {hint}" — hint: A-3 "Low! Go up?", 4-5 "Lowish. Hmm!", 6-8 "Middle-ish. Hmm!", 9-10 "Highish. Hmm!", J-K "High! Go down?" |
| right | "☻ {name} hops! {n} in a row. ♪" |
| tie | "☺ Twins! {name} lets that one slide." |
| wrong | "☺ {card}? Sneaky card! {name} pouts." |
| end | best: "☻ {name} is a card shark now! ♥" · ≥5: "☻ {name} claps its hooves. Nice run! ♪" · else: '☺ {name} giggles. "Again? Again!"' |
| footer (guess) | " h / ▲ higher  ·  l / ▼ lower  ·  q give up" |

---

## 3. Menu (3 games): `menu3.png`
- Three 14x7 cards on rows 2-8 at cols 1 / 18 / 35 (1-col margins, 3-col gaps). Each has a ` n ` REV keycap on its top border, art (3 rows), a bold title on row 6 and a subtitle on row 7.
- Titles: "Which paw?", "Sheep Train", "Higher/Lower". "Higher or Lower" (15 chars) doesn't fit the 12-col inner width, so the card says "Higher/Lower"; the game header says `HIGHER / LOWER`.
- Row 9 under each card: `5 rounds` / `best 23` / `best 9`. Use `new!` before the first run; this is a motivation hook.
- Row 10: "♪ {name} wants to play! Pick one."
- Footer: " 1 2 3 pick  ·  q back".

## Constraints check
- **Glyphs:** only glyphs from the allowed list are used (no ▪ ● ω).
- **No reverse+bold:** I never request REV+BOLD except the header name, which follows the existing pattern.
- **Few cells per frame:**
  - Train: head, neck, tail, lamb, plus 1-2 header/feedback cells per step.
  - Hi/Lo: whole-card redraws happen only on a guess or reveal, as one-shot transitions.

## Unresolved questions
1. Should best scores persist in `pet_state` (per game: `best_train`, `best_hilo`)? The menu and both start screens assume yes.
2. `pet.play_result(won)` takes a bool. To use the reward bands, either pass the score or add `play_result_amount(happy, energy, win)`. Your call.
3. Is the Hi/Lo flip edge frame worth a sub-tick timer, or should the face appear directly? I lean towards direct.
4. Should BIG3 move into `pet_art` (recommended) or be duplicated per game?
