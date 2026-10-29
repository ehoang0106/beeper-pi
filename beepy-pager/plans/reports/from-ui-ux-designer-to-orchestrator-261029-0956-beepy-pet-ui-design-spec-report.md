# Beepy Pet ("Mochi") — UI Design Spec

From: ui-ux-designer → orchestrator · 2026-10-29 · target: Python curses, 50x13 canvas, mono, CP437

All mockups were generated + validated by script: every screen line = exactly 50 cols, every glyph is in the safe list. The `│NN` after each row is just a row-number gutter (not drawn). Ruler at top = column index.

---

## 0. Grid + tokens (use everywhere)

| Token | Value |
|---|---|
| Canvas | 50 cols x 13 rows, origin (row 0, col 0) |
| Gutter | col 0 and col 49 stay blank (except header bar, which is full width reverse) |
| Header | row 0, full-width reverse. Left ` ☻ <Name>` (name reverse+bold). Right `<STAGE> · <age> ` (1 trailing space). Sub-screens: ` ☻ Mochi · play`, ` ☻ Mochi · stats` |
| Stage (pet room) | rows 1-8, cols 1-23. Sprite center col = 12 → `x = 12 - w//2`. Sprite bottom row = 8 (stands on the rule) → `y = 9 - h` |
| Side panel | rows 2-8, cols 25-48 (24 wide) |
| Rule / floor | row 9: col 1 + `─`x48. Doubles as the floor the pet stands on |
| Status line | row 10: col 1 mood glyph (bold), col 3 message (≤46 chars) |
| Action bar | row 11: keycap letter in reverse (1 cell), space, label; 3 spaces between items |
| Footer hint | row 12: home-style, items joined by `  ·  ` |
| Meter | `▓`x filled + `░`x empty + `▌` cap. filled = `round(v*n/100)`. n=12 in panel, n=20 on stats screen (matches home BATT) |
| Panel stat row | `f"{label:<6} {meter(v,12)} {v:>3}"` = 24 cols at col 25. Labels: `FULL` `HAPPY` `ENERGY` `CLEAN` |
| Attributes | R = reverse, B = bold, X = reverse+bold. Never rely on dim |
| Motion | 500 ms tick (2 fps). Redraw only changed cells (curses does this if you don't `clear()`); never blank the full screen |

Age format: `<1h`: `42m`; `<1d`: `5h 03m`; else `6d 04h`. Egg: `EGG · 2m left`.

---

## 1. Main view (adult, hungry, poop on floor)

```
          1111111111222222222233333333334444444444
01234567890123456789012345678901234567890123456789
 ☻ Mochi                           ADULT · 6d 04h │ 0
                   (▲)                            │ 1
                  °      FULL   ▓▓░░░░░░░░░░▌  18 │ 2
        ▄▀▄▄▄▄▄▀▄        HAPPY  ▓▓▓▓▓▓▓▓░░░░▌  64 │ 3
       ▐  •   •  ▌       ENERGY ▓▓▓▓▓▓▓▓▓▓░░▌  81 │ 4
       ▐    o    ▌       CLEAN  ▓▓▓▓▓░░░░░░░▌  40 │ 5
      ▀█         █▀                               │ 6
       ▀▄▄▄▄▄▄▄▄▄▀  ° °   HUNGRY   POOP           │ 7
         ▀▀   ▀▀    ▄█▄                           │ 8
 ──────────────────────────────────────────────── │ 9
 ○ Mochi's tummy is rumbling...                   │10
 f feed   p play   s sleep   c clean   h hug      │11
 pet  ·  i stats  ·  q quit  ·  End Call: menu    │12

attr map (. normal  B bold  R reverse  X reverse+bold):
RXXXXXXXRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR│ 0
..................................................│ 1
.........................BBBBBB...................│ 2
........BBBBBBBBB.................................│ 3
.......B..B...B..B................................│ 4
.......B....B....B................................│ 5
......BB.........BB...............................│ 6
.......BBBBBBBBBBB.......XXXXXXXX.XXXXXX..........│ 7
.........BB...BB..................................│ 8
..................................................│ 9
.B................................................│10
.R........R........R.........R.........R..........│11
..................................................│12
```

Notes:
- Thought bubble `°` + `(▲)` appears beside the head only in **hungry** mood (cols right of sprite, rows above head).
- Poop pile `▄█▄` sits on row 8 at cols 20-22 (2nd poop: cols 2-4; max 2 shown, 3rd+ just keeps the badge). Stink `° °` / ` ° ` alternates on row 7 each tick.
- Panel stat label turns **bold** when value < 25.
- Row 7 badges (reverse+bold, 1 space between): max 2, by priority `SICK` > `HUNGRY` > `TIRED` > `DIRTY` > `SAD` > `POOP`. Threshold: stat < 25 (POOP: any poop). Critical (< 10): that badge blinks (toggle reverse/normal every 2 ticks = 1 s). If more than 2 apply, show 2 + `+1`.
- Status line rotates message every ~8 s (random variant of current mood, §8). Transient action feedback replaces it for 3 s.

### Night / sleeping (teen) — "lights off" room

```
          1111111111222222222233333333334444444444
01234567890123456789012345678901234567890123456789
 ☻ Mochi                            TEEN · 2d 11h │ 0
  °           ·      Z                            │ 1
         ·         Z     FULL   ▓▓▓▓▓▓▓▓░░░░▌  70 │ 2
   ·              z      HAPPY  ▓▓▓▓▓▓▓▓▓░░░▌  77 │ 3
        ▄▀▄▄▄▄▄▀▄        ENERGY ▓▓▓░░░░░░░░░▌  22 │ 4
       ▐  -   -  ▌   °   CLEAN  ▓▓▓▓▓▓▓▓▓▓▓░▌  88 │ 5
       ▐    ·    ▌                                │ 6
 ·      ▀▄▄▄▄▄▄▄▀        zZ asleep 2h 13m         │ 7
         ▀▀   ▀▀                                  │ 8
 ──────────────────────────────────────────────── │ 9
 Z Shh... Mochi is dreaming.                      │10
 f feed   p play   s wake    c clean   h hug      │11
 pet  ·  i stats  ·  q quit  ·  End Call: menu    │12

attr map (. normal  B bold  R reverse  X reverse+bold):
RXXXXXXXRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR│ 0
RRRRRRRRRRRRRRRRRRRRRRRR..........................│ 1
RRRRRRRRRRRRRRRRRRRRRRRR..........................│ 2
RRRRRRRRRRRRRRRRRRRRRRRR..........................│ 3
RRRRRRRRRRRRRRRRRRRRRRRR.BBBBBB...................│ 4
RRRRRRRRRRRRRRRRRRRRRRRR..........................│ 5
RRRRRRRRRRRRRRRRRRRRRRRR..........................│ 6
RRRRRRRRRRRRRRRRRRRRRRRR.BBBBBBBBBBBBBBBB.........│ 7
RRRRRRRRRRRRRRRRRRRRRRRR..........................│ 8
..................................................│ 9
.B................................................│10
...................R...................R..........│11
..................................................│12
```

- Lights-off = reverse video on **stage only** (rows 1-8, cols 0-23), a dark "window card". Sprite + stars drawn inside with reverse attr, so they render as light lines on dark. Panel stays normal — do NOT reverse the meters (reversed `▓`/`░` swap visual weight and read inverted).
- Stars at fixed cells; each tick toggle one random star `·`↔`°` (twinkle). `z` `Z` `Z` drift up-right per §2 Z-frames.
- Panel row 7 shows `zZ asleep <dur>` (bold) instead of badges.
- While asleep: unavailable actions show keycap **non-reversed** (f, p, c). `s` label → `wake ` (padded to keep alignment). `h` stays (tuck-in hug, no wake).
- Optional: if local time 22:00-07:00 and pet awake → `sleepy` mood bias; the room never goes dark unless asleep (dark = asleep, one meaning).

### Egg main view

```
          1111111111222222222233333333334444444444
01234567890123456789012345678901234567890123456789
 ☻ Mochi                            EGG · 2m left │ 0
                                                  │ 1
                         HATCH  ▓▓▓▓▓▓▓░░░░░▌ 58% │ 2
                 °                                │ 3
      ·                  keep it cozy & close     │ 4
          ▄▀▀▀▄          pat it to say hello      │ 5
         ▐ · ° ▌                                  │ 6
        ▐ °   · ▌                                 │ 7
         ▀▄▄▄▄▄▀                                  │ 8
 ──────────────────────────────────────────────── │ 9
 ○ Something is wiggling inside...                │10
 h pat the egg                                    │11
 pet  ·  i stats  ·  q quit  ·  End Call: menu    │12

attr map (. normal  B bold  R reverse  X reverse+bold):
RXXXXXXXRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR│ 0
..................................................│ 1
..................................................│ 2
..................................................│ 3
..................................................│ 4
..........BBBBB...................................│ 5
.........B.B.B.B..................................│ 6
........B.B...B.B.................................│ 7
.........BBBBBBB..................................│ 8
..................................................│ 9
.B................................................│10
.R................................................│11
..................................................│12
```
- Panel shows hatch progress meter (`HATCH`) + 2 hint lines. Only action: `h pat the egg` → plays one wobble burst + random egg message.

---

## 2. Sprites

Sizes (fixed per stage; every mood/frame uses the same box so nothing jumps):

| Stage | W x H | x | y (top) | particle rows |
|---|---|---|---|---|
| EGG | 9 x 4 | 8 | 5 | 1-4 |
| BABY | 9 x 4 | 8 | 5 | 1-4 |
| TEEN | 11 x 5 | 7 | 4 | 1-3 |
| ADULT | 13 x 6 | 6 | 3 | 1-2 |

Sprites are line-art outlines (half-block edges) with a **text-glyph face** inside. Draw sprite cells bold; spaces inside the sprite are NOT drawn (transparent) so particles can pass behind. Faces are templated: `E` = eye (left/right may differ), `M` = mouth, `b` = cheek slot (blank by default).

```
BABY 9x4 template (E=eye, M=mouth, b=cheek slot):
   ▄▀▀▀▀▀▄ 
  ▐ E   E ▌
  ▐ b M b ▌
   ▀▄▄▄▄▄▀ 

TEEN 11x5 template (E=eye, M=mouth, b=cheek slot):
   ▄▀▄▄▄▄▄▀▄ 
  ▐  E   E  ▌
  ▐  b M b  ▌
   ▀▄▄▄▄▄▄▄▀ 
    ▀▀   ▀▀  

ADULT 13x6 template (E=eye, M=mouth, b=cheek slot):
    ▄▀▄▄▄▄▄▀▄  
   ▐  E   E  ▌ 
   ▐ b  M  b ▌ 
  ▀█         █▀
   ▀▄▄▄▄▄▄▄▄▄▀ 
     ▀▀   ▀▀   

```

### Face table (applies to all three stages)

| Mood / frame | Eye L | Eye R | Mouth | Cheek b | Extra |
|---|---|---|---|---|---|
| content (idle A) | `•` | `•` | `u` | ` ` | |
| blink (idle B) | `-` | `-` | `u` | ` ` | |
| happy | `^` | `^` | `▼` | ` ` | `♪ ♫` drift (P-frames) |
| hungry | `•` | `•` | `o` | ` ` | `° (▲)` thought bubble |
| eat A / eat B | `^` | `^` | `O` / `▬` | ` ` | food `▲` beside mouth |
| sad / lonely | `╥` | `╥` | `∩` | ` ` / `°` (tear frame) | |
| sleepy | `_` | `_` | `o` (yawn) ↔ `u` | ` ` | |
| sleeping | `-` | `-` | `·` ↔ `o` (snore) | ` ` | `z Z` |
| dirty | `•` | `•` | `~` | `░` | flies `° ·`, poop |
| sick | `>` | `<` | `~` | ` ` | `≈` fever wave, `°` sweat |
| love (after hug) | `♥` | `♥` | `▼` | ` ` | `♥` particles |
| tease (game: wrong guess) | `^` | `^` | `p` | ` ` | |
| refuse (action denied) | `>` | `<` | `-` | ` ` | sprite x jiggles ±1 for 2 ticks (head shake) |

### Rendered sheets

BABY 9x4 (round mochi blob, no limbs):
```
content     blink       happy       hungry
 ▄▀▀▀▀▀▄     ▄▀▀▀▀▀▄     ▄▀▀▀▀▀▄     ▄▀▀▀▀▀▄
▐ •   • ▌   ▐ -   - ▌   ▐ ^   ^ ▌   ▐ •   • ▌
▐   u   ▌   ▐   u   ▌   ▐   ▼   ▌   ▐   o   ▌
 ▀▄▄▄▄▄▀     ▀▄▄▄▄▄▀     ▀▄▄▄▄▄▀     ▀▄▄▄▄▄▀

eat A       eat B       sad         sleepy
 ▄▀▀▀▀▀▄     ▄▀▀▀▀▀▄     ▄▀▀▀▀▀▄     ▄▀▀▀▀▀▄
▐ ^   ^ ▌   ▐ ^   ^ ▌   ▐ ╥   ╥ ▌   ▐ _   _ ▌
▐   O   ▌   ▐   ▬   ▌   ▐   ∩   ▌   ▐   o   ▌
 ▀▄▄▄▄▄▀     ▀▄▄▄▄▄▀     ▀▄▄▄▄▄▀     ▀▄▄▄▄▄▀

sleeping    dirty       sick        love
 ▄▀▀▀▀▀▄     ▄▀▀▀▀▀▄     ▄▀▀▀▀▀▄     ▄▀▀▀▀▀▄
▐ -   - ▌   ▐ •   • ▌   ▐ >   < ▌   ▐ ♥   ♥ ▌
▐   ·   ▌   ▐ ░ ~ ░ ▌   ▐   ~   ▌   ▐   ▼   ▌
 ▀▄▄▄▄▄▀     ▀▄▄▄▄▄▀     ▀▄▄▄▄▄▀     ▀▄▄▄▄▄▀

tease       refuse
 ▄▀▀▀▀▀▄     ▄▀▀▀▀▀▄
▐ ^   ^ ▌   ▐ >   < ▌
▐   p   ▌   ▐   -   ▌
 ▀▄▄▄▄▄▀     ▀▄▄▄▄▄▀
```

TEEN 11x5 (cat ears + feet):
```
content       blink         happy         hungry
 ▄▀▄▄▄▄▄▀▄     ▄▀▄▄▄▄▄▀▄     ▄▀▄▄▄▄▄▀▄     ▄▀▄▄▄▄▄▀▄
▐  •   •  ▌   ▐  -   -  ▌   ▐  ^   ^  ▌   ▐  •   •  ▌
▐    u    ▌   ▐    u    ▌   ▐    ▼    ▌   ▐    o    ▌
 ▀▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▀
  ▀▀   ▀▀       ▀▀   ▀▀       ▀▀   ▀▀       ▀▀   ▀▀

eat A         eat B         sad           sleepy
 ▄▀▄▄▄▄▄▀▄     ▄▀▄▄▄▄▄▀▄     ▄▀▄▄▄▄▄▀▄     ▄▀▄▄▄▄▄▀▄
▐  ^   ^  ▌   ▐  ^   ^  ▌   ▐  ╥   ╥  ▌   ▐  _   _  ▌
▐    O    ▌   ▐    ▬    ▌   ▐    ∩    ▌   ▐    o    ▌
 ▀▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▀
  ▀▀   ▀▀       ▀▀   ▀▀       ▀▀   ▀▀       ▀▀   ▀▀

sleeping      dirty         sick          love
 ▄▀▄▄▄▄▄▀▄     ▄▀▄▄▄▄▄▀▄     ▄▀▄▄▄▄▄▀▄     ▄▀▄▄▄▄▄▀▄
▐  -   -  ▌   ▐  •   •  ▌   ▐  >   <  ▌   ▐  ♥   ♥  ▌
▐    ·    ▌   ▐  ░ ~ ░  ▌   ▐    ~    ▌   ▐    ▼    ▌
 ▀▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▀
  ▀▀   ▀▀       ▀▀   ▀▀       ▀▀   ▀▀       ▀▀   ▀▀

tease         refuse
 ▄▀▄▄▄▄▄▀▄     ▄▀▄▄▄▄▄▀▄
▐  ^   ^  ▌   ▐  >   <  ▌
▐    p    ▌   ▐    -    ▌
 ▀▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▀
  ▀▀   ▀▀       ▀▀   ▀▀
```

ADULT 13x6 (ears, arms, feet, cheek slots wider):
```
content         blink           happy           hungry
  ▄▀▄▄▄▄▄▀▄       ▄▀▄▄▄▄▄▀▄       ▄▀▄▄▄▄▄▀▄       ▄▀▄▄▄▄▄▀▄
 ▐  •   •  ▌     ▐  -   -  ▌     ▐  ^   ^  ▌     ▐  •   •  ▌
 ▐    u    ▌     ▐    u    ▌     ▐    ▼    ▌     ▐    o    ▌
▀█         █▀   ▀█         █▀   ▀█         █▀   ▀█         █▀
 ▀▄▄▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▄▄▀
   ▀▀   ▀▀         ▀▀   ▀▀         ▀▀   ▀▀         ▀▀   ▀▀

eat A           eat B           sad             sleepy
  ▄▀▄▄▄▄▄▀▄       ▄▀▄▄▄▄▄▀▄       ▄▀▄▄▄▄▄▀▄       ▄▀▄▄▄▄▄▀▄
 ▐  ^   ^  ▌     ▐  ^   ^  ▌     ▐  ╥   ╥  ▌     ▐  _   _  ▌
 ▐    O    ▌     ▐    ▬    ▌     ▐    ∩    ▌     ▐    o    ▌
▀█         █▀   ▀█         █▀   ▀█         █▀   ▀█         █▀
 ▀▄▄▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▄▄▀
   ▀▀   ▀▀         ▀▀   ▀▀         ▀▀   ▀▀         ▀▀   ▀▀

sleeping        dirty           sick            love
  ▄▀▄▄▄▄▄▀▄       ▄▀▄▄▄▄▄▀▄       ▄▀▄▄▄▄▄▀▄       ▄▀▄▄▄▄▄▀▄
 ▐  -   -  ▌     ▐  •   •  ▌     ▐  >   <  ▌     ▐  ♥   ♥  ▌
 ▐    ·    ▌     ▐ ░  ~  ░ ▌     ▐    ~    ▌     ▐    ▼    ▌
▀█         █▀   ▀█         █▀   ▀█         █▀   ▀█         █▀
 ▀▄▄▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▄▄▀
   ▀▀   ▀▀         ▀▀   ▀▀         ▀▀   ▀▀         ▀▀   ▀▀

tease           refuse
  ▄▀▄▄▄▄▄▀▄       ▄▀▄▄▄▄▄▀▄
 ▐  ^   ^  ▌     ▐  >   <  ▌
 ▐    p    ▌     ▐    -    ▌
▀█         █▀   ▀█         █▀
 ▀▄▄▄▄▄▄▄▄▄▀     ▀▄▄▄▄▄▄▄▄▄▀
   ▀▀   ▀▀         ▀▀   ▀▀
```

### Idle motion (all stages)
- Base loop @500 ms: `A A A A B A A A` (blink every ~4 s, randomize ±1 s).
- Hop: every 6-10 s, y-1 for 1 tick, then back (top has 1 spare row in every stage).
- Wander: every ~8 s, x ±1 (clamp to x0 ±2). Never while sleeping/sick.
- Mood faces replace `A`; blink still overlays (except sleeping/love/sick).

### EGG 9x4 — wobble (play E0→E3 @500 ms, 2 cycles, then rest 4-6 s)
```
E0 rest     E1 lean L   E2 rest     E3 lean R
  ▄▀▀▀▄      ▄▀▀▀▄        ▄▀▀▀▄        ▄▀▀▀▄
 ▐ · ° ▌    ▐ · ° ▌      ▐ · ° ▌      ▐ · ° ▌
▐ °   · ▌   ▐ °   · ▌   ▐ °   · ▌   ▐ °   · ▌
 ▀▄▄▄▄▄▀     ▀▄▄▄▄▄▀     ▀▄▄▄▄▄▀     ▀▄▄▄▄▄▀
```

### Hatching (H0→H4 @500 ms; hold H3 1 s; H4 is BABY happy). Shows 1 extra row above (lid flies up).
```
H0 rest    H1 crack   H2 crack+  H3 peek    H4 hello!
                        ·   ·      ▄▀▀▀▄    ·   ☼   ·
  ▄▀▀▀▄      ▄▀▀▀▄      ▄▀▀▀▄      ▀▀▀▀▀     ▄▀▀▀▀▀▄
 ▐ · ° ▌    ▐ ·/° ▌    ▐ /\/ ▌    ▐▄▀▄▀▄▌   ▐ ^   ^ ▌
▐ °   · ▌  ▐ °   · ▌  ▐ °\  · ▌  ▐  • •  ▌  ▐   ▼   ▌
 ▀▄▄▄▄▄▀    ▀▄▄▄▄▄▀    ▀▄▄▄▄▄▀    ▀▄▄▄▄▄▀    ▀▄▄▄▄▄▀
```
Sequence: 3x wobble bursts → H1 → wobble → H2 → H3 (lid up, eyes peek) → H4 (lid gone, `☼` sparkle) → status `{n} says hello, world!` + LED flash. Header flips `EGG` → `BABY · <1m`.

---

## 3. Action feedback animations

Snippets show the stage only: 23 cols x 8 rows = screen cols 1-23, rows 1-8 (snippet row 0 = screen row 1). Shown on ADULT; for other stages anchor particles to the sprite box (mouth row, head top, sides), same relative offsets.

**Feed `f`** — onigiri `▲` drops (F1 head-height right, F2 beside face, F3 next to mouth while chomping), F4 crumbs, F5 `nom!`. Then FULL meter ticks up 1 cell per tick (animated fill, 3-4 ticks).
```
F1                       F2                       F3 chomp
                 ▲

       ▄▀▄▄▄▄▄▀▄                ▄▀▄▄▄▄▄▀▄                ▄▀▄▄▄▄▄▀▄
      ▐  •   •  ▌              ▐  •   •  ▌▲             ▐  ^   ^  ▌
      ▐    o    ▌              ▐    o    ▌              ▐    O▲   ▌
     ▀█         █▀            ▀█         █▀            ▀█         █▀
      ▀▄▄▄▄▄▄▄▄▄▀              ▀▄▄▄▄▄▄▄▄▄▀              ▀▄▄▄▄▄▄▄▄▄▀
        ▀▀   ▀▀                  ▀▀   ▀▀                  ▀▀   ▀▀

F4 chew                  F5 yum
                                        nom!

       ▄▀▄▄▄▄▄▀▄                ▄▀▄▄▄▄▄▀▄
      ▐  ^   ^  ▌              ▐  ^   ^  ▌
      ▐    ▬    ▌              ▐    ▼    ▌
     ▀█   ·  ·  █▀            ▀█         █▀
      ▀▄▄▄▄▄▄▄▄▄▀              ▀▄▄▄▄▄▄▄▄▄▀
        ▀▀   ▀▀                  ▀▀   ▀▀
```

**Hug `h`** — hearts rise from above head; eyes become `♥`; settle with sparkles. Each `♥` moves up 1 row per tick, disappears at row 1.
```
H1                       H2                       H3
                                  ♥                   ·        ♥
          ♥                           ♥                 ♥
       ▄▀▄▄▄▄▄▀▄                ▄▀▄▄▄▄▄▀▄                ▄▀▄▄▄▄▄▀▄
      ▐  ^   ^  ▌              ▐  ♥   ♥  ▌              ▐  ♥   ♥  ▌
      ▐    ▼    ▌              ▐    ▼    ▌              ▐    ▼    ▌
     ▀█         █▀            ▀█         █▀            ▀█         █▀
      ▀▄▄▄▄▄▄▄▄▄▀              ▀▄▄▄▄▄▄▄▄▄▀              ▀▄▄▄▄▄▄▄▄▄▀
        ▀▀   ▀▀                  ▀▀   ▀▀                  ▀▀   ▀▀

H4 settle
      ·          ·

       ▄▀▄▄▄▄▄▀▄
      ▐  ^   ^  ▌
      ▐    u    ▌
     ▀█         █▀
      ▀▄▄▄▄▄▄▄▄▄▀
        ▀▀   ▀▀
```

**Clean `c`** — eyes close, bubbles `o O °` spawn around sides and rise 1 row/tick, popping to `·`; poop + flies + `░` cheeks vanish at C3; C4 `√` sparkle.
```
C1 suds                  C2 rise                  C3 pop

                             ·                      ·
       ▄▀▄▄▄▄▄▀▄                ▄▀▄▄▄▄▄▀▄                ▄▀▄▄▄▄▄▀▄   °
    ° ▐  -   -  ▌          °   ▐  -   -  ▌              ▐  ^   ^  ▌ o
      ▐ ░  o  ░ ▌              ▐    o    ▌  o           ▐    u    ▌
  o  ▀█         █▀            ▀█         █▀ O          ▀█         █▀
      ▀▄▄▄▄▄▄▄▄▄▀  O           ▀▄▄▄▄▄▄▄▄▄▀              ▀▄▄▄▄▄▄▄▄▄▀
        ▀▀   ▀▀                  ▀▀   ▀▀                  ▀▀   ▀▀

C4 sparkle
   ·
                √
       ▄▀▄▄▄▄▄▀▄
      ▐  ^   ^  ▌
      ▐    ▼    ▌
     ▀█         █▀
      ▀▄▄▄▄▄▄▄▄▄▀
        ▀▀   ▀▀
```

**Sleep `s`** — stage flips to reverse (night card) in one redraw, then Z-loop. Wake: one frame `☼` at head-top right, face `^ ▼`, stage back to normal.
```
Z1                       Z2                       Z3 snore
                                            Z                        Z
                 z                        z                           z
       ▄▀▄▄▄▄▄▀▄                ▄▀▄▄▄▄▄▀▄                ▄▀▄▄▄▄▄▀▄
      ▐  -   -  ▌              ▐  -   -  ▌              ▐  -   -  ▌
      ▐    ·    ▌              ▐    ·    ▌              ▐    o    ▌
     ▀█         █▀            ▀█         █▀            ▀█         █▀
      ▀▄▄▄▄▄▄▄▄▄▀              ▀▄▄▄▄▄▄▄▄▄▀              ▀▄▄▄▄▄▄▄▄▄▀
        ▀▀   ▀▀                  ▀▀   ▀▀                  ▀▀   ▀▀
```

**Ambient mood loops** (2 frames each, alternate @500 ms):
```
D1 flies+poop            D2
               ·              ·
    °                                    °
       ▄▀▄▄▄▄▄▀▄                ▄▀▄▄▄▄▄▀▄
      ▐  •   •  ▌              ▐  •   •  ▌
      ▐ ░  ~  ░ ▌              ▐ ░  ~  ░ ▌
     ▀█         █▀            ▀█         █▀
      ▀▄▄▄▄▄▄▄▄▄▀  ° °         ▀▄▄▄▄▄▄▄▄▄▀   °
        ▀▀   ▀▀    ▄█▄           ▀▀   ▀▀    ▄█▄
```
```
S1 fever                 S2
        ≈                         ≈
               °
       ▄▀▄▄▄▄▄▀▄                ▄▀▄▄▄▄▄▀▄
      ▐  >   <  ▌              ▐  >   <  ▌ °
      ▐    ~    ▌              ▐    ~    ▌
     ▀█         █▀            ▀█         █▀
      ▀▄▄▄▄▄▄▄▄▄▀              ▀▄▄▄▄▄▄▄▄▄▀
        ▀▀   ▀▀                  ▀▀   ▀▀
```
```
sad A                    sad B tear


       ▄▀▄▄▄▄▄▀▄                ▄▀▄▄▄▄▄▀▄
      ▐  ╥   ╥  ▌              ▐  ╥   ╥  ▌
      ▐    ∩    ▌              ▐ °  ∩  ° ▌
     ▀█         █▀            ▀█         █▀
      ▀▄▄▄▄▄▄▄▄▄▀              ▀▄▄▄▄▄▄▄▄▄▀
        ▀▀   ▀▀                  ▀▀   ▀▀
```
```
P1                       P2
    ♪                                      ♫
                 ♫            ♪
       ▄▀▄▄▄▄▄▀▄                ▄▀▄▄▄▄▄▀▄
      ▐  ^   ^  ▌              ▐  ^   ^  ▌
      ▐    ▼    ▌              ▐    ▼    ▌
     ▀█         █▀            ▀█         █▀
      ▀▄▄▄▄▄▄▄▄▄▀              ▀▄▄▄▄▄▄▄▄▄▀
        ▀▀   ▀▀                  ▀▀   ▀▀
```

**Poop event**: pet face `^ u`, then `▄█▄` appears at next free slot with stink; status `Oops. {n} made a little mess.`

**Stage-up**: 3 ticks alternating old/new sprite (both bottom-aligned), then `☼` sparkle at head-top + status message + LED white flash.

---

## 4. Play mini-game: "Which paw?"

Rules: 5 rounds; Mochi shuffles a treat `▲` between two paws (cards), then hides it; guess `l`eft / `r`ight. 3+ correct = win. Costs ENERGY -10 always; HAPPY +20 win / +5 lose (nobody feels bad). Blocked if ENERGY < 15 (refuse face + message).

Round flow (ticks @500 ms): show `▲` in left card → right → left/right random (3-5 swaps, faster: 400 ms) → both cards `?` → wait for key (no timeout) → reveal 1.5 s → next round.

Start:
```
          1111111111222222222233333333334444444444
01234567890123456789012345678901234567890123456789
 ☻ Mochi · play                        WHICH PAW? │ 0
                                                  │ 1
                                                  │ 2
  Mochi hides a     ▄▀▄▄▄▄▄▀▄       5 rounds      │ 3
  treat ▲ in one   ▐  ^   ^  ▌      3 to win      │ 4
  paw. Guess it!   ▐    ▼    ▌      +HAPPY ♥      │ 5
                  ▀█         █▀                   │ 6
                   ▀▄▄▄▄▄▄▄▄▄▀                    │ 7
                     ▀▀   ▀▀                      │ 8
 ──────────────────────────────────────────────── │ 9
 ♪ Mochi is ready to play!                        │10
 p start                                          │11
 play  ·  any key: start  ·  q back               │12

attr map (. normal  B bold  R reverse  X reverse+bold):
RXXXXXXXXXXXXXXRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR│ 0
..................................................│ 1
..................................................│ 2
....................BBBBBBBBB.....................│ 3
...................B..B...B..B....................│ 4
...................B....B....B....................│ 5
..................BB.........BB...................│ 6
...................BBBBBBBBBBB....................│ 7
.....................BB...BB......................│ 8
..................................................│ 9
.B................................................│10
.R................................................│11
..................................................│12
```

In play (awaiting guess):
```
          1111111111222222222233333333334444444444
01234567890123456789012345678901234567890123456789
 ☻ Mochi · play                         round 3/5 │ 0
                which paw? hmm...                 │ 1
                                                  │ 2
   ┌───────┐        ▄▀▄▄▄▄▄▀▄         ┌───────┐   │ 3
   │       │       ▐  •   •  ▌        │       │   │ 4
   │   ?   │       ▐    u    ▌        │   ?   │   │ 5
   │       │      ▀█         █▀       │       │   │ 6
   └───────┘       ▀▄▄▄▄▄▄▄▄▄▀        └───────┘   │ 7
     l left          ▀▀   ▀▀           r right    │ 8
 ──────────────────────────────────────────────── │ 9
 score  ♥ ○ ·  · ·                need 3 to win   │10
                                                  │11
 l left  ·  r right  ·  q give up                 │12

attr map (. normal  B bold  R reverse  X reverse+bold):
RXXXXXXXXXXXXXXRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR│ 0
................BBBBBBBBBBBBBBBBB.................│ 1
..................................................│ 2
....................BBBBBBBBB.....................│ 3
...................B..B...B..B....................│ 4
...................B....B....B....................│ 5
..................BB.........BB...................│ 6
...................BBBBBBBBBBB....................│ 7
.....R...............BB...BB...........R..........│ 8
..................................................│ 9
..................................................│10
..................................................│11
..................................................│12
```
- Cards = box-drawn 9x5 at cols 3-11 and 38-46, rows 3-7. Labels row 8.
- Score row 10: `♥` correct, `○` miss, `·` pending (5 pips, space-separated; a double space before the not-yet-played group is fine but optional).

Reveal (correct, guessed right):
```
          1111111111222222222233333333334444444444
01234567890123456789012345678901234567890123456789
 ☻ Mochi · play                         round 3/5 │ 0
                      ♪  ♫                        │ 1
                                                  │ 2
   ┌───────┐        ▄▀▄▄▄▄▄▀▄         ┌───────┐   │ 3
   │       │       ▐  ^   ^  ▌        │       │   │ 4
   │   ·   │       ▐    ▼    ▌        │   ▲   │   │ 5
   │       │      ▀█         █▀       │       │   │ 6
   └───────┘       ▀▄▄▄▄▄▄▄▄▄▀        └───────┘   │ 7
                     ▀▀   ▀▀         √ found it!  │ 8
 ──────────────────────────────────────────────── │ 9
 score  ♥ ○ ♥  · ·                need 3 to win   │10
                                                  │11
 next round in a sec...                           │12

attr map (. normal  B bold  R reverse  X reverse+bold):
RXXXXXXXXXXXXXXRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR│ 0
..................................................│ 1
..................................................│ 2
....................BBBBBBBBB.........XXXXXXXXX...│ 3
...................B..B...B..B........XXXXXXXXX...│ 4
...................B....B....B........XXXXXXXXX...│ 5
..................BB.........BB.......XXXXXXXXX...│ 6
...................BBBBBBBBBBB........XXXXXXXXX...│ 7
.....................BB...BB.........BBBBBBBBBBB..│ 8
..................................................│ 9
..................................................│10
..................................................│11
..................................................│12
```
- Chosen card turns reverse+bold (whole 9x5 box, X). Correct: card shows `▲`, pet happy + `♪ ♫`, row 8 under card `√ found it!` bold. Wrong: chosen card shows `·`, the other card flips to `▲` (normal attr), pet `tease` face (`^ p`), row 8 `nope!`.

Win:
```
          1111111111222222222233333333334444444444
01234567890123456789012345678901234567890123456789
 ☻ Mochi · play                             3 / 5 │ 0
             ♥                      ·             │ 1
                  █ █ ▄▀▄ █ █ █                   │ 2
                   █  █▀█  █  ▄                   │ 3
                                  ♥               │ 4
                    ♥ ♥ ○ ♥ ○                     │ 5
                                                  │ 6
          +20 HAPPY   -10 ENERGY   +1 win         │ 7
                                                  │ 8
 ──────────────────────────────────────────────── │ 9
 ☻ Mochi does a tiny victory dance.               │10
                                                  │11
 p again  ·  any key: back                        │12

attr map (. normal  B bold  R reverse  X reverse+bold):
RXXXXXXXXXXXXXXRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR│ 0
..................................................│ 1
..................B.B.BBB.B.B.B...................│ 2
...................B..BBB..B..B...................│ 3
..................................................│ 4
..................XXXXXXXXXXXXX...................│ 5
..................................................│ 6
..........BBBBBBBBB...............................│ 7
..................................................│ 8
..................................................│ 9
.B................................................│10
..................................................│11
..................................................│12
```
Lose:
```
          1111111111222222222233333333334444444444
01234567890123456789012345678901234567890123456789
 ☻ Mochi · play                             1 / 5 │ 0
                                                  │ 1
                 █▀█ █▀█ █▀█ ▄▀▀                  │ 2
                 █▄█ █▄█ █▀▀ ▄▄▀                  │ 3
                                                  │ 4
                    ○ ♥ ○ ○ ○                     │ 5
                                                  │ 6
        +5 HAPPY    -10 ENERGY   fun anyway       │ 7
                                                  │ 8
 ──────────────────────────────────────────────── │ 9
 ☺ Mochi giggles. "Again? Again!"                 │10
                                                  │11
 p again  ·  any key: back                        │12

attr map (. normal  B bold  R reverse  X reverse+bold):
RXXXXXXXXXXXXXXRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR│ 0
..................................................│ 1
.................BBB.BBB.BBB.BBB..................│ 2
.................BBB.BBB.BBB.BBB..................│ 3
..................................................│ 4
..................XXXXXXXXXXXXX...................│ 5
..................................................│ 6
........BBBBBBBB..................................│ 7
..................................................│ 8
..................................................│ 9
.B................................................│10
..................................................│11
..................................................│12
```
- Big words use a 3x2-cell half-block font (same family as the home clock digits), bold. Glyphs: Y=`█ █`/` █ `, A=`▄▀▄`/`█▀█`, !=`█`/`▄`, O=`█▀█`/`█▄█`, P=`█▀█`/`█▀▀`, S=`▄▀▀`/`▄▄▀`; 1 col gap between letters.
- Pip summary = reverse+bold card cols 18-30, row 5.
- Win: hearts at cols 13/34/36 twinkle (`♥`↔`·`) for 4 ticks.

---

## 5. Special screens

### First-run naming
```
          1111111111222222222233333333334444444444
01234567890123456789012345678901234567890123456789
 ☻ new friend                              hello! │ 0
                               °                  │ 1
                 ·    ▄▀▀▀▄                       │ 2
                     ▐ · ° ▌                      │ 3
                    ▐ °   · ▌   ·                 │ 4
                     ▀▄▄▄▄▄▀                      │ 5
                                                  │ 6
       A warm egg appeared. What's its name?      │ 7
                                                  │ 8
           NAME   Mochi█     max 8                │ 9
                                                  │10
                                                  │11
 type a name  ·  Enter: done  ·  Bksp: erase      │12

attr map (. normal  B bold  R reverse  X reverse+bold):
RXXXXXXXXXXXXRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR│ 0
..................................................│ 1
......................BBBBB.......................│ 2
.....................B.B.B.B......................│ 3
....................B.B...B.B.....................│ 4
.....................BBBBBBB......................│ 5
..................................................│ 6
.......BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB......│ 7
..................................................│ 8
.................RRRRRRRRRRR......................│ 9
..................................................│10
..................................................│11
..................................................│12
```
- Field: reverse, cols 17-27 (11 cells: 1 pad + 8 chars + cursor + pad). Cursor `█` blinks each tick (`█`↔` `). Default text `Mochi` pre-filled and selected: first keypress replaces it. Allowed: letters, digits, space, `-`; max 8. Enter on empty = `Mochi`. Egg wobbles while typing (E-frames), giving life to a form.

### Info / stats (`i`)
```
          1111111111222222222233333333334444444444
01234567890123456789012345678901234567890123456789
 ☻ Mochi · stats                   ADULT · 6d 04h │ 0
                                                  │ 1
 FULL    ▓▓▓▓░░░░░░░░░░░░░░░░▌  18  ↓ 4/h         │ 2
 HAPPY   ▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░▌  64  ↓ 3/h         │ 3
 ENERGY  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░▌  81  ↑ 9/h         │ 4
 CLEAN   ▓▓▓▓▓▓▓▓░░░░░░░░░░░░▌  40  ↓ 2/h         │ 5
 ──────────────────────────────────────────────── │ 6
 BORN   Oct 23  9:14a     MOOD   hungry           │ 7
 MEALS  42                HUGS   118              │ 8
 GAMES  9 / 14 won        CLEANS 17               │ 9
 NAPS   6                 NEXT   all grown up     │10
                                                  │11
 stats  ·  any key: back  ·  q quit               │12

attr map (. normal  B bold  R reverse  X reverse+bold):
RXXXXXXXXXXXXXXXRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR│ 0
..................................................│ 1
.BBBBBB...........................................│ 2
..................................................│ 3
..................................................│ 4
..................................................│ 5
..................................................│ 6
.BBBB.....................BBBB....................│ 7
.BBBBB....................BBBB....................│ 8
.BBBBB....................BBBBBB..................│ 9
.BBBB.....................BBBB....................│10
..................................................│11
..................................................│12
```
- 20-cell meters identical to home `BATT` style. Trend = change per hour over the last hour (`↑`/`↓`/`→`). `NEXT`: `teen in 1d 3h` / `adult in 6h` / `all grown up`.

### Ran away to Grandma's
```
          1111111111222222222233333333334444444444
01234567890123456789012345678901234567890123456789
 ☻ empty room                              6d 04h │ 0
                                                  │ 1
    ┌────────────────────────────────────────┐    │ 2
    │ Dear you,                            ¶ │    │ 3
    │ I got hungry and a bit lonely, so I    │    │ 4
    │ went to stay with Grandma. She makes   │    │ 5
    │ the best rice balls. Come visit me! ♥  │    │ 6
    │                            - Mochi     │    │ 7
    └────────────────────────────────────────┘    │ 8
                                                  │ 9
 Mochi stayed 6d 4h · 42 meals · 118 hugs         │10
                                                  │11
 n new egg  ·  q quit                             │12

attr map (. normal  B bold  R reverse  X reverse+bold):
RXXXXXXXXXXXXRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR│ 0
..................................................│ 1
..................................................│ 2
..................................................│ 3
..................................................│ 4
..................................................│ 5
..................................................│ 6
..................................................│ 7
..................................................│ 8
..................................................│ 9
..................................................│10
..................................................│11
..................................................│12
```
- Note card box: cols 4-45, rows 2-8. Before showing the note, 3-tick transition: empty stage (no sprite) with a lone `¶` on the floor at col 12, status `Mochi's room is quiet... there's a note.` Then the note.
- `n` → naming screen (new egg). LED off.
- Variant line 2 by cause: hungry: `I got hungry and a bit lonely, so I` · dirty: `My room got too messy, so I`. Keep each note line ≤ 38 chars inside the box.

---

## 6. Action bar + footer

| Context | Row 11 action bar | Row 12 footer |
|---|---|---|
| Normal | ` f feed   p play   s sleep   c clean   h hug` | ` pet  ·  i stats  ·  q quit  ·  End Call: menu` |
| Asleep | f, p, c keycaps non-reversed; `s wake ` | same |
| Egg | ` h pat the egg` | same |
| Play | (row 11 blank) | ` l left  ·  r right  ·  q give up` |
| Stats | (blank) | ` stats  ·  any key: back  ·  q quit` |
| Ran away | (blank) | ` n new egg  ·  q quit` |

Key press feedback: pressed keycap shows **normal** (un-reversed) for 1 tick = "pressed" flash, then the action anim starts. During an action anim (≤ 3 s) other action keys are queued max 1, not dropped silently.

---

## 7. LED (RGB 0-255)

| State | RGB | Behaviour |
|---|---|---|
| egg | (255, 140, 40) warm amber | breathe: 100% 1 s / 30% 1 s |
| hatch moment | (255, 255, 255) | 3 quick flashes (250 ms) then → happy |
| happy | (0, 255, 80) green | steady |
| content | (0, 180, 160) teal | steady |
| love (hug, 3 s) | (255, 40, 140) pink | 3 blinks 250 ms, then return to mood |
| hungry | (255, 110, 0) orange | slow blink 1 s on / 1 s off |
| sad / lonely | (40, 60, 255) blue | steady |
| sleepy | (130, 60, 220) lavender | steady |
| sleeping | (20, 0, 60) deep indigo | steady, very dim |
| dirty | (150, 150, 0) olive | steady |
| sick | (255, 0, 0) red | blink 500 ms on / 500 ms off |
| playing | (0, 220, 255) cyan | steady; win: 3x green flash; lose: 1x orange flash |
| stage-up | (255, 255, 255) | 2 flashes then mood |
| ran away | (0, 0, 0) | off |
| game quit | restore pager's previous LED state | — |

Priority when several moods are true: sick > hungry > dirty > sad > sleepy > happy > content (sleeping overrides all except sick). Status glyph + face use the same winner, so LED, face, glyph and copy always agree. Apply a global brightness scale (e.g. 0.4) if the LED is harsh at night.

---

## 8. Micro-copy

Status glyph per mood (row 10, col 1, bold): happy `☻` · content `☺` · hungry `○` · sad `▼` · sleepy `z` · sleeping `Z` · dirty `≈` · sick `+` · love `♥` · egg `○` · play `♪`.

| Mood / event | Messages (`{n}` = pet name, ≤8 chars; all ≤46 cols with 8-char name) |
|---|---|
| happy (☻) | `{n} is bouncing off the walls!`<br>`{n} wiggles happily. ♪`<br>`Best day ever, says {n}.`<br>`{n} does a tiny victory dance.` |
| content (☺) | `{n} is humming a little song.`<br>`{n} watches the clouds go by.`<br>`All good. {n} blinks at you.`<br>`{n} is just vibing.` |
| hungry (○) | `{n}'s tummy is rumbling...`<br>`{n} is eyeing your snacks. [f]`<br>`{n} dreams of rice balls ▲`<br>`Feed me? {n} looks hopeful.` |
| sad / lonely (▼) | `{n} misses you. A hug? [h]`<br>`{n} sighs at the window.`<br>`{n} wants someone to play with.`<br>`Kinda quiet in here...` |
| sleepy (z) | `{n} is yawning big yawns.`<br>`{n} rubs their eyes. Bed? [s]`<br>`Eyelids getting heavy...`<br>`{n} nods off mid-blink.` |
| sleeping (Z) | `Shh... {n} is dreaming.`<br>`zzz... {n} snores softly.`<br>`{n} dreams of flying rice balls.` |
| dirty (≈) | `{n} is a little stinky. [c]`<br>`Flies are visiting {n}...`<br>`Bath time? {n} is smudgy.`<br>`Uh oh. Somebody pooped. [c]` |
| sick (+) | `{n} feels wobbly. Needs care!`<br>`{n} has the sniffles...`<br>`{n} isn't well. Food & rest help.` |
| love (♥) | `{n} loves you this much! ♥`<br>`♥ ♥ ♥  {n} melts into the hug.`<br>`{n} snuggles in. So warm.` |
| egg (○) | `Something is wiggling inside...`<br>`The egg feels warm.`<br>`Tap tap... was that a heartbeat?` |
| action: feed ok | `Nom nom nom! ▲`<br>`{n} licks the plate clean.` |
| action: feed refused | `{n} is stuffed! Maybe later.` |
| action: clean | `Squeaky clean! √`<br>`Sparkly! {n} smells like soap.` |
| action: clean (nothing) | `Already sparkling clean! √` |
| action: sleep / wake | `Lights out. Sweet dreams, {n}.`<br>`Good morning, {n}! ☼` |
| action: blocked while asleep | `Shh, {n} is asleep. [s] wakes` |
| action: play refused | `{n} is too sleepy to play.` |
| event: poop | `Oops. {n} made a little mess.` |
| event: grew up | `{n} grew up! Now a TEEN.`<br>`{n} is all grown up! ADULT.` |
| event: hatched | `{n} says hello, world!` |
| event: welcome back | `{n} missed you! Away 3h 12m.` |

Ran-away memorial line (row 10): `{n} stayed <age> · <meals> meals · <hugs> hugs`.

---

## 9. Design principles applied
- **One grid, one rhythm**: header / stage+panel / rule-floor / status / actions / footer — same rows on every screen; sub-screens reuse header + footer so the eye never re-learns.
- **Matches `home`**: reverse header bar, `▓░▌` meters, 48-col `─` rule, `  ·  ` footer, reverse badges.
- **Line-art sprites + text faces**: outlines from half-blocks stay crisp on the memory LCD; faces use real glyphs so 14 moods only cost a 3-char swap per stage (DRY templates, no per-mood art).
- **Reverse = meaning**: reverse is reserved for header, keycaps, warnings, chosen/result cards, and the night room. Nothing decorative is reversed.
- **Calm motion**: ≤ 2 fps, small particles, no full-screen flashes; only the stage card flips on sleep/wake (one redraw).
- **Redundant signals**: mood shown by face + glyph + copy + LED; warnings by badge + bold label + meter.
- **Kind failure**: no death, losing the mini-game still gives +HAPPY, runaway is a letter not a grave.

## 10. Glyph / legibility risks
1. `╥` (sad eyes) is CP437 0xD2 but in the "mixes" family — verify it renders; fallback `T`.
2. `▼` mouth + `^` eyes at 8x16 font: `^` may be small; fallback eyes `ⁿ` (CP437 0xFC) look like closed happy arcs — test both on device.
3. Bold may not change half-block glyphs at all on the console font — harmless, but don't rely on bold for sprite readability.
4. `░` cheek smudge (dirty) next to `~` could look noisy at baby size; fallback `·`.
5. Reverse night card: verify the Sharp LCD/terminal does not ghost when 192 cells flip at once; if it does, flip the stage in 2 ticks (top half, then bottom half) as a "curtain" effect.
6. `≈`, `°`, `·` are tiny; they're used only as secondary particles, never as sole meaning.
7. Name with wide/odd chars: restrict to ASCII (naming screen rules) so header width math holds.
8. Header right text longest: `ADULT · 99d 23h ` = 16 cols; name ≤8 → left ≤10. Fits.

## Unresolved questions
1. Sick recovery: no medicine action — should sick clear automatically once all stats > 25 (recommended), or should `h`/`f` explicitly cure?
2. Is the `End Call: menu` footer item still correct inside the game (does the game run under the same tmux/menu wrapper as home)?
3. Hug cooldown? Spamming `h` would farm HAPPY; suggest diminishing returns (UI: love anim plays shorter, copy `{n} is already super loved!`).
4. Touchpad arrows: optionally map ←/→ to l/r in the mini-game (free affordance) — confirm.
