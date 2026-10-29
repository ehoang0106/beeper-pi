"""'Higher or Lower' mini-game: guess whether the next card is higher or lower.
A tie is a free pass; one wrong guess ends the run. Score = streak of right guesses.

Pure state machine; pet_screens_hilo draws it.
Phases: intro -> guess -> reveal -> guess ... -> (wrong) reveal -> end
"""

import random

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]  # A is low
SUITS = ["♥", "♦", "♣", "♠"]
KEY_GUESS = {"h": "higher", "UP": "higher", "l": "lower", "DOWN": "lower"}
REVEAL_FRAMES = 3  # 1.5 s at the game's 500 ms tick


def value(card):
    return RANKS.index(card[0])


class HiLoGame:
    def __init__(self, rng=random):
        self.rng = rng
        self.phase = "intro"
        self.deck = []
        self.current = None
        self.next_card = None
        self.history = []   # earlier cards, oldest first
        self.streak = 0
        self.result = None  # "right", "tie" or "wrong" for the last reveal
        self.guess = None
        self.frame = 0
        self.reveal_frame = 0

    def start(self):
        self.__init__(self.rng)
        self.current = self._draw()
        self.phase = "guess"

    def _draw(self):
        if not self.deck:
            self.deck = [(r, s) for r in RANKS for s in SUITS]
            self.rng.shuffle(self.deck)
        return self.deck.pop()

    def key(self, key):
        """h / l (or touchpad up / down) during a guess."""
        guess = KEY_GUESS.get(key)
        if self.phase != "guess" or guess is None:
            return
        self.guess, self.next_card = guess, self._draw()
        diff = value(self.next_card) - value(self.current)
        if diff == 0:
            self.result = "tie"
        elif (diff > 0) == (guess == "higher"):
            self.result = "right"
            self.streak += 1
        else:
            self.result = "wrong"
        self.phase, self.reveal_frame = "reveal", self.frame

    def step(self):
        """Advance one 500 ms tick. Returns True when the run just ended."""
        self.frame += 1
        if self.phase == "reveal" and self.frame - self.reveal_frame >= REVEAL_FRAMES:
            return self.next()
        return False

    def next(self):
        """Leave the reveal early (any key) or on its own. Returns True when the run ended."""
        if self.phase != "reveal":
            return False
        if self.result == "wrong":
            self.phase = "end"
            return True
        self.history = (self.history + [self.current])[-5:]
        self.current, self.next_card, self.phase = self.next_card, None, "guess"
        return False
