# Shaun-inspired sheep sprites: design report

Deliverables (all in /tmp/claude-1000/sheep/):
- `shaun_sprites.py`: pure data, `TEMPLATES`, `MASKS`, `FACES` (all 16 keys)
- `shaun_final_baby.png`, `shaun_final_teen.png`, `shaun_final_adult.png`: 16 expressions each, real 24x8 room, real Beepy font
- `shaun_final_night.png`: all stages on the reversed (night) room
- Tooling: `sandbox2.py` (room-accurate renderer, contract `check()`), `px.py` (pixel-grid to half-block converter), `s10.py` (design source), `make_final.py`, `render_final.py`

## Sizes (contract checked: equal rows, mask same shape, 2xE, 1xM, 2xb)
| stage | WxH | b slots |
|---|---|---|
| baby | 13x6 | yes |
| teen | 15x7 | yes |
| adult | 19x7 | yes |
All 3 are odd widths, so the mouth sits exactly on the centre column and stays centred at x = 12 - w//2.

## Design vs the references
- **Shared eye system:** each eye is a light (unmasked) cell holding the pupil glyph. Whites get extra light from half-blocks above and below (`▀` / `▄`). Content pupil `■` = black pupil in a white eye. The engine's blink `-` reads as a closed lid.
- **Baby (bead art 11.png):** square dark head; wide "goggles" (two 3-cell white boxes with a dark bridge); horizontal floppy ears at the top corners; nostrils `∙ ∙` flanking the mouth on a dark muzzle band; round white body; grey `▒` arms; two dark feet.
- **Teen:** the baby head grows a small wool dome on top. The goggles split into two separate rounded (cross-shaped) eyes. Ears drop to eye level and droop. The face lengthens. The body gets a wavy wool outline and legs.
- **Adult (Shaun 12.png):** big wool cap with a zig-zag fringe over the forehead; long thick ears out to the sides with drooping tips; two round white eyes close together; long dark face with nostrils at the end of the muzzle; woolly zig-zag body sides; two chunky legs.
- The cheek slot `b` sits on the dark face under each eye (R-masked). The `sad_tear` `°` shows as a light tear and `dirty` `░` as smudges.
- Mouth `M` and nostrils `∙` are R-masked: light glyphs on the dark face by day.

## Night mode
Every dark cell (half-blocks, R cells) inverts, so night shows a clean light-on-dark negative of the same sheep. Eyes become dark cells with light pupils, and all expressions still read (see the night PNG).

## Risks / notes
- Light areas (wool cap, body, goggles) are transparent spaces, so anything drawn in the room behind the sprite shows through. That is the same behaviour as the current sprites.
- In the baby template, two R-masked cells beside `M` are spaces in the art (row 3, cols 5 and 7). They are drawn dark only because of the mask, so keep the mask paired with the template.
- `▬`, `■`, `╥`, `♥`, `°`, `░`, `▼`, `∩` and `∙` were checked in the real font. `●` and `ω` are NOT in the font (they render as ?), so neither is used.
- The face table changed (content eyes are now `■`, sleepy eyes `▬`). Any other sprites that share FACES will change with it.

## Unresolved questions
- Should egg/hatch art be restyled to match? (Out of scope; not touched.)
- Does the dark arms dither `▒` on the baby look acceptable on the real LCD? Dithers can shimmer on memory LCDs, so check on the device.
