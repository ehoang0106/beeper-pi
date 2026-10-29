# home: pet line design (ui-ux-designer -> orchestrator)

Date 2026-10-29. Goal: add a minimal pet line to the `home` screen (50x13, mono LCD). Recommended: **Option A** (one labelled `PET` row; IP moves onto the WIFI row).

## Options considered (previews in /tmp/claude-1000/sheep/)
| Opt | Idea | Cost | Verdict |
|---|---|---|---|
| A | `PET` row in BATT/WIFI block (row 7); IP folded into WIFI row, right-aligned | SSID limit 24 -> 14 chars | **Recommended**. Uses the same label column as BATT/WIFI, keeps the blank row 4 under the clock, no other change |
| B | Pet line with no label in the blank row 4 under the clock | Clock runs straight into BATT, no breathing room; reads as part of the clock side column | Rejected (crowded, see home_B_all.png) |
| C | CPU/LOAD/MEM/DISK on one row, pet row + 10-cell care meter below | Stats row already 50/50 cols, breaks when DISK grows (`12G/235G`); a meter is more pet info than asked for | Rejected |

Files: `home_A_all.png`, `home_B_all.png`, `home_C_all.png` (each holds 7 states), text mockups with ruler `home_{A,B,C}.txt`. Final: `home_final_all.png` (10 states), `home_final.txt`. Generators: `home_mock.py`, `home_mock_final.py`.

## Recommended layout (Option A)
```
0         1         2         3         4         5
01234567890123456789012345678901234567890123456789
 ■ beeper                               up 1h 35m      row0  REV (unchanged)
  ▀█  ▀█  ▄ █ █ █▀▀   │ Thursday                       rows1-3 BOLD clock (unchanged)
   █   █  ▄ ▀▀█ ▀▀█   │ 29 October 2026
  ▀▀▀ ▀▀▀     ▀ ▀▀▀   │ ■ 68°F  Patchy rain nearby
                                                       row4 blank (kept)
 BATT ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░▌  86%  4.06V                row5 unchanged
 WIFI ▓▓░░  Awaken               11.0.0.88  -73dBm     row6 CHANGED: IP added
 PET  ○ Mochi     TEEN · 3d 04h            [ HUNGRY ]  row7 NEW (replaces IP row)
 ────────────────────────────────────────────────      rows 8-12 unchanged
 CPU  38°C               LOAD 0.09
 MEM  132/424M           DISK 2.4G/235G
 ────────────────────────────────────────────────
 home -w live  ·  bat  ·  hold End Call: menu
```
Legend: `[ X ]` = reverse span (RV ... R0, never with BD). Everything else on rows 5-12 is normal weight.

### What moved or changed
- `IP` row removed. The IP is now right-aligned on the WIFI row, ending 8 cols before the dBm value.
- The SSID pad drops from 24 to 14 chars (it is cut at 14).
- New `PET` row at row 7. Nothing else changes, footer included.

### Row 6, WIFI (replace the current `wifi()` printf)
Connected:
```bash
printf '%s  %s %15s %7s' "$bars" "$(padr "$ssid" 14)" "${ip:---}" "${lvl:-?}dBm"
```
Not connected: `printf '····  %s' "$(padr 'not connected' 14)"` and leave the IP out. In the preview a lone `--` right-aligned looked stray. If you'd rather keep the IP for USB networking, use `%15s` like the connected case.
In `draw()`: drop `printf ' %-5s%s\n' "IP" ...` and pass `$ip` into `wifi` (or make it a global).
Width: 1+5 + 4+2+14+1+15+1+7 = 50.

### Row 7, PET
Column map: label 1-4, glyph 6, name 8-15 (pad 8), stage·age 18-32 (pad 15), mood word 35-42, badge right-aligned so it ends at col 49.
```bash
# NAME pad 8, SA = "STAGE · AGE" pad 15
left=$(printf ' %-5s%s %s  %s' "PET" "$glyph" "$(padr "$name" 8)" "$(padr "$SA" 15)")   # 33 cols
if [ -n "$badge" ]; then                       # urgent: the badge replaces the mood word
    b=" $badge "                                # e.g. " HUNGRY " (8)
    printf '%s%*s%s%s%s\n' "$left" $((W - 33 - ${#b})) '' "$RV" "$b" "$R0"
else
    printf '%s  %s\n' "$left" "$mood"          # mood word, max 8 ("sleeping")
fi
```
Note: `padr` counts characters, so `·` and glyphs pad correctly. Do not use `%-15s` on strings with multibyte characters.

### Exact text per state
| State | Row 7 text (cols from 0) |
|---|---|
| happy | ` PET  ☻ Mochi     BABY · 2h 05m    happy` |
| content | ` PET  ☺ Shaunsy1  ADULT · 99d 23h  content` |
| sleepy | `... z ... sleepy` |
| asleep | ` PET  Z Mochi     ADULT · 12d 06h  sleeping` (Z glyph + word; no TIRED badge while already asleep) |
| hungry | ` PET  ○ Mochi     TEEN · 3d 04h` + badge ` HUNGRY ` at cols 42-49 |
| sad | glyph ▼, badge ` SAD ` (else word `sad`) |
| dirty | glyph ≈, badge ` POOP ` or ` DIRTY ` (else word `dirty`) |
| sick | glyph +, badge ` SICK ` |
| tired | glyph z, badge ` TIRED ` |
| egg | ` PET  ○ Mochi     EGG · hatch 12m` (no mood word). If 60m or more: `EGG · hatch 1h` (whole hours, so it stays within 15) |
| ran away | ` PET  ○ Mochi     ran away to Grandma · type pet` (48 cols, no badge) |
| no pet (state file missing) | ` PET  ·  no sheep yet · type pet to adopt` |
| helper error / unreadable state | ` PET  ·  --` (fail quietly; home must never break) |

Rules:
- Show at most ONE badge: the helper's most urgent one.
- If there is a badge, leave the mood word out (the badge already says it). Otherwise show the mood word.
- Age comes from the helper as is (`2h 05m`, `3d 04h`). The worst case, `ADULT · 99d 23h`, is exactly 15. Ages of 100 days or more would need `ADULT · 100d` (drop the hours).
- Stage is always uppercase. The `·` separator is the same glyph already used in the footer.
- Glyphs used: ☻ ☺ ○ ▼ z Z ≈ + ·. All are in the verified font list. The PNGs confirm they render (☻ shows as a filled face, ○ as a small ring).

## Validation
- Every state rendered in the real 8x16 PSF font (home_final_all.png). The widest line is exactly 50 cols (checked by script).
- Reverse badges sit on normal rows, so reverse is never combined with bold.
- The badge's right edge lines up with the weather and dBm text at col 49. The reverse block is the only dark spot below the header, so an urgent need is visible at a glance.
- Live mode (`home -w`, 30s refresh) needs nothing extra. The pet line just refreshes with the rest.

## Unresolved questions
1. Glyph mapping: 10 moods but 9 glyphs were given. I assumed happy☻ content☺ hungry○ sad▼ sleepy z sleeping Z dirty≈ sick+ gone○ egg○. Should the helper provide the glyph, or should home map it?
2. Is cutting the SSID to 14 chars acceptable? (Current SSID "Awaken" is fine.)
3. When there is no Wi-Fi, should the IP still show (e.g. USB gadget networking)?
4. Optional: add `pet` to the footer hint (` home -w live · pet · bat · hold End Call: menu`, 47 cols, single spacing around ·). Not done because it changes the established footer spacing.
