"""'Which paw?' mini-game: 5 rounds of guessing which paw hides the treat, 3 to win.

Pure state machine driven by tick() and guess(); pet_screens_other draws it.
Phases: intro -> (shuffle -> guess -> reveal) x5 -> end
"""

import random

ROUNDS = 5
WINS_NEEDED = 3
REVEAL_TICKS = 3  # 1.5 s at 500 ms per tick


class Game:
    def __init__(self, rng=random):
        self.rng = rng
        self.phase = "intro"
        self.round = 0
        self.results = []
        self.treat = "l"
        self.choice = None
        self.correct = False
        self.shuffle = []
        self.phase_tick = 0

    def start(self, t):
        self.__init__(self.rng)
        self._next_round(t)

    def _next_round(self, t):
        self.round += 1
        # Flair: the treat hops left, right, then a few random paws. Where it really
        # ends up is picked separately, so watching the shuffle doesn't give it away.
        self.shuffle = ["l", "r"] + [self.rng.choice("lr") for _ in range(self.rng.randint(3, 5))]
        self.treat = self.shuffle[0]
        self.phase = "shuffle"
        self.phase_tick = t

    def tick(self, t):
        """Advance timed phases. Returns True when the game just ended."""
        step = t - self.phase_tick
        if self.phase == "shuffle":
            if step < len(self.shuffle):
                self.treat = self.shuffle[step]
            else:
                self.treat = self.rng.choice("lr")
                self.phase = "guess"
        elif self.phase == "reveal" and step >= REVEAL_TICKS:
            if self.round < ROUNDS:
                self._next_round(t)
            else:
                self.phase = "end"
                return True
        return False

    def guess(self, side, t):
        if self.phase != "guess":
            return
        self.choice = side
        self.correct = side == self.treat
        self.results.append(self.correct)
        self.phase = "reveal"
        self.phase_tick = t

    def won(self):
        return sum(self.results) >= WINS_NEEDED
