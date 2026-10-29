"""'Sheep Train' mini-game (snake): Mochi walks a fenced field collecting lost lambs,
who follow in a line. Hitting the fence or the train ends the run.

Pure state machine on a grid of cells; pet_screens_train draws it.
Phases: intro -> playing -> crashed (short "bonk") -> end
"""

import random
from collections import deque

DIRS = {"UP": (0, -1), "DOWN": (0, 1), "LEFT": (-1, 0), "RIGHT": (1, 0)}
KEY_DIRS = {"w": "UP", "s": "DOWN", "a": "LEFT", "d": "RIGHT",
            "UP": "UP", "DOWN": "DOWN", "LEFT": "LEFT", "RIGHT": "RIGHT"}
START_LEN = 3
SLOWEST, FASTEST = 0.30, 0.15  # seconds per step
SPEEDUP_PER_LAMB = 0.01
CRASH_FRAMES = 4  # the "bonk" moment before the game-over screen


class TrainGame:
    def __init__(self, width, height, rng=random):
        self.w, self.h, self.rng = width, height, rng
        self.phase = "intro"
        self.train = deque()  # (x, y) cells, head first
        self.facing = "RIGHT"
        self.queued = []      # turns typed faster than the train moves, applied one per step
        self.lamb = None
        self.score = 0
        self.frame = 0
        self.crash_frame = 0
        self.eat_frame = -99  # frame of the last lamb collected (for the 'baa!' flash)

    def start(self):
        self.__init__(self.w, self.h, self.rng)
        y, x = self.h // 2, self.w // 4
        self.train = deque((x - i, y) for i in range(START_LEN))
        self.phase = "playing"
        self._place_lamb()

    def step_seconds(self):
        return max(FASTEST, SLOWEST - self.score * SPEEDUP_PER_LAMB)

    def _place_lamb(self):
        free = [(x, y) for x in range(self.w) for y in range(self.h) if (x, y) not in self.train]
        self.lamb = self.rng.choice(free) if free else None

    def key(self, key):
        """Queue a turn. Reversing straight into the train is ignored."""
        d = KEY_DIRS.get(key)
        if self.phase != "playing" or d is None:
            return
        last = self.queued[-1] if self.queued else self.facing
        dx, dy = DIRS[d]
        lx, ly = DIRS[last]
        if (dx, dy) != (-lx, -ly) and d != last and len(self.queued) < 2:
            self.queued.append(d)

    def step(self):
        """Advance one frame. Returns True when the run just ended (game-over screen)."""
        self.frame += 1
        if self.phase == "crashed":
            if self.frame - self.crash_frame >= CRASH_FRAMES:
                self.phase = "end"
                return True
            return False
        if self.phase != "playing":
            return False
        if self.queued:
            self.facing = self.queued.pop(0)
        dx, dy = DIRS[self.facing]
        hx, hy = self.train[0]
        head = (hx + dx, hy + dy)
        eating = head == self.lamb
        body = list(self.train) if eating else list(self.train)[:-1]  # the tail moves away
        if not (0 <= head[0] < self.w and 0 <= head[1] < self.h) or head in body:
            self.phase, self.crash_frame = "crashed", self.frame
            return False
        self.train.appendleft(head)
        if eating:
            self.score += 1
            self.eat_frame = self.frame
            self._place_lamb()
            if self.lamb is None:  # filled the whole field: a perfect run
                self.phase, self.crash_frame = "crashed", self.frame
        else:
            self.train.pop()
        return False
