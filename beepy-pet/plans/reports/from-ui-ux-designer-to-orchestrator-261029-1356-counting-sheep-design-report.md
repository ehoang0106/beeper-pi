# Counting Sheep: design spec (screens, sprites, paths, copy)

Date 2026-10-29 · for: orchestrator · fan-art mini-game for Mochi (Shaun-style sheep)

## Artifacts (all in /tmp/claude-1000/sheep/)
| File | What |
|---|---|
| `count_sprites.py` | **Pure data** (no imports): sheep frames + masks, fence, jump path, coward sequence, reveal icons, sky/stars, menu art, input box, round tuning, rewards |
| `count_mock.py` | Reference renderer for every screen. Copy the draw logic from here (helpers match `pet_screens_main` header/rule/status/footer) |
| `count_mockups.txt` | All 12 screens as 50x13 text grids with a column ruler and an attribute grid (`.` normal `B` bold `R` reverse `X` rev+bold) |
| `count_<screen>.png` | Real-font renders: menu, intro, intro-baby, parade, parade-peak, answer, answer-empty, reveal-ok, reveal-wrong, reveal-wrong-max, end-win, end-lose. `count_all.png` = everything stacked |
| `count_kit.py`, `count_try*.py/png` | Scratch exploration (can be ignored) |

## 1. Sprites (see `count_sprites.py` for exact strings)

**Sheep, 6x2, facing right.** I rendered and compared 8 options. This one read as "Shaun" best:
```
▒▒▒▒°▄    ▒ = grey wool, ° = eye on an inverted (mask R) dark head, ▄ = dark muzzle
║  ║      ║ = a pair of thin legs in one cell
```
Mask: `["    R ", "      "]` → the head cell is drawn dark with a light eye on the light field. Blit with `c.sprite(row, col, rows, BOLD, mask)`.

| Frame | Row 2 (legs) | Use |
|---|---|---|
| walk_a | `║  ║  ` | walk, alternate with walk_b every step |
| walk_b | ` ║ ║  ` | mid-stride (legs shift 1 col; `║║` side by side blurred into 3 legs, so I rejected it) |
| jump_up | `/  /  ` | rising, legs trailing |
| jump_top | `▀  ▀  ` | peak, legs tucked |
| jump_down | `\  \  ` | falling, legs reaching forward |
| stand | `║  ║  ` | hesitating at the fence |

Left-facing (cowards): `▄°▒▒▒▒` / `  ║  ║` and `  ║ ║ `; mask `[" R    ", "      "]`.
Bubble (`?` / `!`, BOLD): one row above the sheep, over the head: col + 4 when facing right, col + 1 when facing left.

**Fence, 5x3**, NORMAL, top-left (6, 22), centred on col 24:
```
┬─┬─┬
┼─┼─┼
│ │ │
```
The ground rule on row 9 gets `┴` at cols 22, 24 and 26, so the posts look planted.

## 2. Motion

- Grounded sheep: top-left row 7 (body row 7, legs row 8). Enters at col -6 (clipped), exits past col 50.
- Walking: 1 col per tick, alternating walk_a and walk_b.
- **Jump**: a sheep at dx = col - 22 = **-8** takes off. Then step through `JUMP_PATH`, 15 ticks of `(dy, dx, frame)`:
  `(-1,-7,up) (-2,-6,up) (-3,-5,up) (-3,-4,up) (-4,-3,top) … (-4,2,top) (-3,3,down) (-3,4,down) (-2,5,down) (-1,6,down) (0,7,walk_a)`
  Horizontal speed stays 1 col per tick, so it never lurches. The peak is at rows 3-4. While the sprite overlaps the fence columns, its legs are always above row 6 (checked by script). **Count the jump at the touch-down tick.**
- **Coward** stops at dx = -8 (col 14), then `COWARD_SEQ`: stand 1 tick → `?` 3 ticks → looks back (L, `?`) 1 tick → looks at the fence (R, `?`) 1 tick → turns (L, `!`) 2 ticks → scurries left at 2 cols per tick.
- **No collisions:** while a coward is retreating, the spawner holds the next sheep until the coward is off-screen. Never make the first sheep of a round a coward. Minimum spawn gap is 8 cols (sprite is 6 wide).
- Only the moving sheep (about 12-16 cells) and 1-2 twinkling stars change per tick, which suits the memory LCD.

**Timing / round tuning (`ROUNDS`):**
| Round | Sheep (incl. cowards) | Cowards | Sec per step | Spawn gap (cols) |
|---|---|---|---|---|
| 1 | 4-6 | 0 | 0.22 | next sheep spawns when the previous one touches down (one approaching at a time) |
| 2 | 6-9 | 1 | 0.18 | 14-20 |
| 3 | 8-12 | 2-3 | 0.15 | 8-14 (two on screen, overlapping jump and approach) |

Estimated parade length: R1 about 35-40 s, R2 about 30 s, R3 about 30 s. Pauses: wait 0.6 s after the last sheep leaves before the answer screen. The reveal auto-advances after 3 s (any key skips). The input cursor and stars use the existing 0.5 s tick.

## 3. Screens (full grids + attributes in `count_mockups.txt`)

Shared conventions: header ` ■ Mochi · play` with right-side `round N/3 ` (or `pick a game ` / `COUNTING SHEEP ` / `N / 3 `); footer hints on row 12. The deviation is that during rounds, **row 10 = narration** (glyph + text, home-screen style) and **row 11 = score pips** `score  ♥ ○ ·` + `need 2 to win`.

| Screen | Layout |
|---|---|
| menu | Two 22-wide cards, cols 2-23 and 26-47, rows 2-8. Keycap ` 1 ` / ` 2 ` in reverse on the top border. Mini art (paw cards / sheep jumping a fence) on rows 3-5, bold title row 6, subtitle row 7, info row 9 |
| intro | Mirrors the Which-paw intro: Mochi happy, centred at col 25. Rules text left at col 2 (rows 3-5), facts right at col 37. Row 10 warns about chickens. Row 11 shows `p` start |
| parade | Night sky band on rows 1-2 (REV fill, ○ moon at col 43, twinkling stars), light field on rows 3-8, fence, ground rule. Mock shows a jumper descending, a coward with `?`, one walking in and one walking out. `parade-peak` shows a jumper at peak and a coward turning with `!` |
| answer | No sky. Mochi sprite at the left (content face, home position col 12). Right: bold `How many sheep` / `jumped over?` (rows 3-4). Input box REV at (6, 26), 6 wide: ` 7_  ` + `sheep`. Hint `type a number` on row 8. At most 2 digits; Enter with an empty box is ignored |
| reveal ok / wrong | Big `YAY!` / `OOPS` (`pet_art.big_text`) at (2, 2). Text at col 20 on rows 2-3. **Replay-free truth:** a lane of right-facing 3x2 mini sheep (one per jumper) on rows 5-6, a blank row 7, then left-facing cowards on rows 8-9. Reveal screens drop the row-9 rule so the lanes stay apart. Pitch 4 cols, max 12 icons = cols 1-47 |
| end win / lose | Same as `_draw_play_end`: header `N / 3 `, centred big word on rows 2-3, pips card REV on row 5, rewards on row 7. Twinkles use night stars `° ·` instead of ♥. Status glyph `z` (sleepy) |

**Mochi placement:** full sprite on the intro and answer screens, face glyph in the narration line everywhere else. Mochi is left out of the parade on purpose: the sprite is 13-19 cols wide and the sheep need the whole 50-col field to enter, jump and exit at readable sizes.

## 4. Micro-copy (all ≤46 cols with an 8-char name; `{n}` = name)

| State | Copy |
|---|---|
| menu | row 1 bold `What shall we play?` · status `♪ {n} wants to play! Pick one.` · footer ` 1 / 2 pick  ·  q back` · card 2 `Counting Sheep` / `count the jumpers` / `3 rounds · sleepy z` |
| intro | `Sheep hop` / `the fence.` / `Count them!` · `3 rounds` / `2 to win` / `+HAPPY ♥` · status `! Some chicken out. Don't count those!` · footer ` play  ·  any key: start  ·  q back` |
| parade | status `♪ {n} counts along... shh.` (alt: `☺ Eyes on the fence...`, `z One sheep... two sheep...`) · footer ` just watch & count  ·  q give up` |
| answer | bold `How many sheep` / `jumped over?` · `type a number` · status `? {n} lost count at 3. You got it?` (number = random 2-4 for flavour) · footer ` 0-9 type  ·  Enter: done  ·  Bksp: erase` |
| reveal ok | `√ yes! {N} jumped over.` / `you said {N} · {k} got scared` (drop the `· …` part when k = 0) · status `☻ {n} claps its hooves! ♪` |
| reveal wrong, off by 1 | `so close, it was {N}!` / `you said {G} · {k} got scared` |
| reveal wrong, off by 2+ | `it was {N}!` / same second line |
| wrong-copy status | if guess > truth and cowards: `☺ Psst... {k} chickened out. Sneaky!`; otherwise `☺ Sheep are slippery. {n} giggles.` |
| reveal footer | ` next round in a sec...  ·  any key: go` |
| end win | `+{h} HAPPY   -5 ENERGY   +1 win` · status `z {n} yawns... all that counting! Nap?` |
| end lose | `+{h} HAPPY    -5 ENERGY   cozy anyway` · status `z {n} yawns. Sheep win this time. zzz` |
| end footer | ` p again  ·  any key: back` |

Rewards (`REWARDS`): 3/3 → +20, 2/3 → +15 (win at 2 or more), 1/3 → +8, 0/3 → +5 HAPPY. Always -5 ENERGY. Suggest also nudging the pet's sleepiness and showing its sleepy face on return.

## 5. Rationale

- **Light field with a dark sky band.** Grey `▒` wool with a dark head reads as Shaun only on a light background. Inside the reverse band the masks flip (light head), so sheep never enter rows 1-2: the peak is at row 3. The band plus stars and moon gives the bedtime mood at a cost of 2 rows.
- **One horizontal speed for walking and jumping**, plus a long flat peak, gives a floaty, dreamy hop, and it is easy to count because each jump lasts 15 ticks.
- **The reveal reuses the scene's own language.** Right-facing sheep went over, left-facing sheep ran away. The player sees why they were off without a replay.
- **`_` cursor instead of `█`.** In a REV box, `█` renders as a light block that looks like a gap (seen in the render; the existing naming screen has the same quirk).
- Score was moved to row 11 so row 10 can carry Mochi's narration, which is consistent with the home screen.

## 6. Risks

- **Speed / LCD ghosting.** 0.15 s per step in R3 is at the stated limit. If ghosting appears, keep 0.18 s and make R3 harder with a smaller gap and more cowards instead.
- **Counting fairness.** In R3 a coward's `?` pause (6 ticks ≈ 0.9 s) plus holding spawns stretches the parade. That is fine, but don't shorten the `?` below 3 ticks or cowards become unreadable.
- **REV_BOLD header name.** The canvas already strips bold on reverse cells (mock checker flagged only those cells; harmless).
- **Leg glyphs `/` `\`** are thin. They read fine in the real font at 2x preview; check on the device.
- **Mask semantics.** If a sheep ever overlaps the REV sky band, its head inverts. The path keeps the peak at row 3, so don't raise it.
- **Wide numbers.** Totals stay ≤12, so input is limited to 2 digits. Ignore a leading zero, or accept `07` as 7.

## Unresolved questions

1. Should `q` during the parade forfeit the whole game (count as a loss, still costing ENERGY), or just return to the menu with no rewards?
2. Should the menu remember the last game (e.g. Enter = replay last), or keep number-only selection as briefed?
3. Should Counting Sheep be playable while Mochi is asleep (bedtime theme), or blocked like Which paw? (`{n} is too sleepy to play.`)
4. Should the end screen actually raise sleepiness / lower energy beyond -5 (the "gets sleepy" effect), or only show it in copy?
