"""A 50x13 cell buffer with normal/bold/reverse attributes, flushed to curses.

Screens draw into a fresh Canvas every tick; curses only sends the cells that
changed, which keeps the Sharp memory LCD from flickering.
"""

import curses

W, H = 50, 13
NORMAL, BOLD, REV = 0, 1, 2
REV_BOLD = BOLD | REV


class Canvas:
    def __init__(self):
        self.cells = [[(" ", NORMAL) for _ in range(W)] for _ in range(H)]

    def text(self, row, col, s, attr=NORMAL):
        """Write a string; characters past the edges are clipped."""
        if not 0 <= row < H:
            return
        for i, ch in enumerate(s):
            if 0 <= col + i < W:
                self.cells[row][col + i] = (ch, attr)

    def sprite(self, row, col, rows, attr=BOLD, mask=None):
        """Blit art with spaces as transparent cells (they keep what's underneath).

        Cells marked R in `mask` are always drawn, inverted against what's under
        them: dark on a light room, light on the dark night room.
        """
        for dy, line in enumerate(rows):
            for dx, ch in enumerate(line):
                solid = mask is not None and mask[dy][dx] == "R"
                if (ch != " " or solid) and 0 <= row + dy < H and 0 <= col + dx < W:
                    _, under = self.cells[row + dy][col + dx]
                    flip = REV if solid else 0
                    self.cells[row + dy][col + dx] = (ch, attr | ((under & REV) ^ flip))

    def fill(self, row, col, w, h, attr):
        """Set the attribute of a block of cells, e.g. the reverse night room."""
        for r in range(row, min(row + h, H)):
            for c in range(col, min(col + w, W)):
                ch, _ = self.cells[r][c]
                self.cells[r][c] = (ch, attr)

    def bar(self, row, attr=REV):
        """Full-width bar (the header)."""
        self.fill(row, 0, W, 1, attr)

    def flush(self, win, top, left):
        """Draw onto a curses window at an offset, batching runs of equal attributes."""
        for r, line in enumerate(self.cells):
            c = 0
            while c < W:
                attr = line[c][1]
                end = c
                while end < W and line[end][1] == attr:
                    end += 1
                run = "".join(ch for ch, _ in line[c:end])
                try:
                    win.addstr(top + r, left + c, run, _curses_attr(attr))
                except curses.error:
                    pass  # writing the very last cell of the window raises; harmless
                c = end

    def lines(self):
        """Plain text rows, for tests."""
        return ["".join(ch for ch, _ in line) for line in self.cells]


def _curses_attr(attr):
    # The Linux console draws bold as "bright", which in reverse video turns into a
    # light background with light text: invisible on the Beepy's LCD. Reverse wins.
    if attr & REV:
        return curses.A_REVERSE
    return curses.A_BOLD if attr & BOLD else curses.A_NORMAL
