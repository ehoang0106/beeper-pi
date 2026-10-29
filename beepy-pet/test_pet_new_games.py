"""Tests for Sheep Train and Higher or Lower state machines."""

import random
import unittest

from pet_hilo_game import HiLoGame, value
from pet_train_game import CRASH_FRAMES, FASTEST, START_LEN, TrainGame


class FixedRng(random.Random):
    """choice() returns a preset cell so lamb placement is predictable."""
    def __init__(self, cells):
        super().__init__(0)
        self.cells = list(cells)

    def choice(self, seq):
        return self.cells.pop(0) if self.cells else seq[0]


class TestTrain(unittest.TestCase):
    def game(self, lambs=()):
        g = TrainGame(10, 6, FixedRng(lambs))
        g.start()
        return g

    def test_moves_and_keeps_length(self):
        g = self.game([(9, 0)])
        head = g.train[0]
        g.step()
        self.assertEqual(g.train[0], (head[0] + 1, head[1]))
        self.assertEqual(len(g.train), START_LEN)

    def test_eats_lamb_grows_and_speeds_up(self):
        hx, hy = 2, 3
        g = self.game([(hx + 1, hy), (9, 0)])
        before = g.step_seconds()
        g.step()
        self.assertEqual((g.score, len(g.train)), (1, START_LEN + 1))
        self.assertLess(g.step_seconds(), before)
        g.score = 99
        self.assertEqual(g.step_seconds(), FASTEST)

    def test_cannot_reverse_into_itself(self):
        g = self.game([(9, 0)])
        g.key("a")  # facing RIGHT: LEFT is ignored
        g.step()
        self.assertEqual(g.facing, "RIGHT")
        self.assertEqual(g.phase, "playing")

    def test_two_quick_turns_are_queued(self):
        g = self.game([(9, 0)])
        g.key("w")
        g.key("a")  # up then left: a U-turn done properly over two steps
        g.step()
        self.assertEqual(g.facing, "UP")
        g.step()
        self.assertEqual(g.facing, "LEFT")
        self.assertEqual(g.phase, "playing")

    def test_wall_crash_then_end(self):
        g = self.game([(9, 0)])
        while g.phase == "playing":
            g.step()
        self.assertEqual(g.phase, "crashed")
        ended = False
        for _ in range(CRASH_FRAMES):
            ended = g.step() or ended
        self.assertTrue(ended)
        self.assertEqual(g.phase, "end")

    def test_self_crash(self):
        g = self.game([(9, 0)])
        g.train = type(g.train)([(5, 3), (4, 3), (4, 4), (5, 4), (6, 4), (6, 3)])
        g.facing = "DOWN"  # head (5,3) moves into (5,4): its own body
        g.step()
        self.assertEqual(g.phase, "crashed")

    def test_moving_into_the_tail_cell_is_allowed(self):
        g = self.game([(9, 0)])
        g.train = type(g.train)([(5, 3), (5, 4), (4, 4), (4, 3)])  # tail at (4,3), head next to it
        g.facing = "LEFT"
        g.step()
        self.assertEqual(g.phase, "playing")

    def test_controls_ignored_outside_play(self):
        g = TrainGame(10, 6)
        g.key("w")
        self.assertEqual((g.phase, g.queued), ("intro", []))


class TestHiLo(unittest.TestCase):
    def game(self, cards):
        """`cards` are dealt in order (first = starting card)."""
        g = HiLoGame()
        g.start()
        g.current = cards[0]
        g.deck = list(reversed(cards[1:]))
        return g

    def test_right_guesses_build_a_streak(self):
        g = self.game([("5", "♥"), ("9", "♠"), ("2", "♣")])
        g.key("h")
        self.assertEqual((g.result, g.streak), ("right", 1))
        g.next()
        self.assertEqual((g.phase, g.current), ("guess", ("9", "♠")))
        g.key("DOWN")
        self.assertEqual((g.result, g.streak, g.history), ("right", 2, [("5", "♥")]))

    def test_tie_is_a_free_pass(self):
        g = self.game([("7", "♥"), ("7", "♠")])
        g.key("l")
        self.assertEqual((g.result, g.streak), ("tie", 0))
        self.assertFalse(g.next())
        self.assertEqual(g.phase, "guess")

    def test_wrong_guess_ends_after_reveal(self):
        g = self.game([("K", "♥"), ("A", "♠")])
        g.key("h")
        self.assertEqual(g.result, "wrong")
        ended = False
        for _ in range(5):
            ended = g.step() or ended
        self.assertTrue(ended)
        self.assertEqual(g.phase, "end")

    def test_ace_is_low_and_deck_reshuffles(self):
        self.assertLess(value(("A", "♠")), value(("2", "♥")))
        g = HiLoGame(random.Random(4))
        g.start()
        seen = 0
        while g.phase != "end" and seen < 200:
            g.key("h" if value(g.current) < 7 else "l")
            g.next()
            seen += 1
        self.assertGreater(seen, 0)

    def test_keys_ignored_outside_guess(self):
        g = HiLoGame()
        g.key("h")
        self.assertEqual(g.phase, "intro")


if __name__ == "__main__":
    unittest.main()
