"""Tests for pet_state: run with `python3 -m unittest test_pet_state` in this folder."""

import os
import random
import tempfile
import unittest

import pet_state
from pet_state import HOUR, Pet

T0 = 1_800_000_000.0
HATCHED = T0 + pet_state.EGG_SECONDS


class NoPoop(random.Random):
    def random(self):
        return 1.0


class TestStages(unittest.TestCase):
    def test_stage_by_age(self):
        pet = Pet(born=T0, updated=T0)
        self.assertEqual(pet.stage(T0 + 60), "egg")
        self.assertEqual(pet.stage(HATCHED + 1), "baby")
        self.assertEqual(pet.stage(T0 + 2 * 24 * HOUR), "teen")
        self.assertEqual(pet.stage(T0 + 4 * 24 * HOUR), "adult")

    def test_egg_does_not_decay(self):
        pet = Pet(born=T0, updated=T0)
        pet.advance(T0 + 60, NoPoop())
        self.assertEqual(pet.fullness, 80)

    def test_decay_starts_at_hatch_not_birth(self):
        pet = Pet(born=T0, updated=T0)
        pet.advance(HATCHED + HOUR, NoPoop())
        self.assertAlmostEqual(pet.fullness, 80 - 8)


class TestDecay(unittest.TestCase):
    def test_awake_decay_rates(self):
        pet = Pet(born=T0, updated=HATCHED)
        pet.advance(HATCHED + 2 * HOUR, NoPoop())
        self.assertAlmostEqual(pet.fullness, 80 - 16)
        self.assertAlmostEqual(pet.happy, 80 - 12)
        self.assertAlmostEqual(pet.energy, 80 - 10)
        self.assertAlmostEqual(pet.clean, 100 - 8)

    def test_sleep_restores_energy_and_wakes_when_full(self):
        pet = Pet(born=T0, updated=HATCHED, energy=50, asleep=True)
        pet.advance(HATCHED + 3 * HOUR, NoPoop())
        self.assertEqual(pet.energy, 100)
        self.assertFalse(pet.asleep)

    def test_partial_hours_are_exact(self):
        pet = Pet(born=T0, updated=HATCHED)
        pet.advance(HATCHED + 1800, NoPoop())
        self.assertAlmostEqual(pet.fullness, 76)

    def test_stats_never_go_negative(self):
        pet = Pet(born=T0, updated=HATCHED)
        pet.advance(HATCHED + 20 * HOUR, NoPoop())
        for stat in pet_state.STATS:
            self.assertGreaterEqual(getattr(pet, stat), 0)


class TestNeglect(unittest.TestCase):
    def test_gets_sick_after_a_stat_sits_at_zero(self):
        pet = Pet(born=T0, updated=HATCHED, fullness=0)
        pet.advance(HATCHED + 7 * HOUR, NoPoop())
        self.assertTrue(pet.sick)
        self.assertEqual(pet.mood(), "sick")

    def test_runs_away_after_long_neglect(self):
        pet = Pet(born=T0, updated=HATCHED)
        pet.advance(HATCHED + 4 * 24 * HOUR, NoPoop())
        self.assertTrue(pet.ran_away)
        self.assertEqual(pet.mood(), "gone")

    def test_care_resets_neglect_clock(self):
        pet = Pet(born=T0, updated=HATCHED, fullness=0, happy=0)
        pet.advance(HATCHED + 10 * HOUR, NoPoop())
        pet.fullness = pet.happy = pet.energy = pet.clean = 100
        pet.advance(HATCHED + 11 * HOUR, NoPoop())
        self.assertEqual(pet.neglect_hours, 0)
        self.assertFalse(pet.ran_away)

    def test_poop_appears_and_hurts_clean(self):
        always = random.Random()
        always.random = lambda: 0.0
        pet = Pet(born=T0, updated=HATCHED)
        pet.advance(HATCHED + HOUR, always)
        self.assertEqual(pet.poops, 1)


class TestActions(unittest.TestCase):
    def test_feed(self):
        pet = Pet(fullness=50)
        self.assertEqual(pet.feed(), "ate")
        self.assertEqual(pet.fullness, 80)
        self.assertEqual(Pet(fullness=99).feed(), "full")
        self.assertEqual(Pet(asleep=True).feed(), "asleep")

    def test_play_and_tired(self):
        pet = Pet(happy=50, energy=50)
        pet.play_result(True)
        self.assertEqual((pet.happy, pet.energy, pet.games, pet.wins), (70, 40, 1, 1))
        pet.play_result(False)
        self.assertEqual((pet.happy, pet.games, pet.wins), (75, 2, 1))
        self.assertEqual(Pet(energy=10).can_play(), "tired")

    def test_hug_diminishing_returns(self):
        pet = Pet(happy=0)
        self.assertEqual(pet.hug(T0), "loved")
        pet.hug(T0 + 10)
        pet.hug(T0 + 20)
        self.assertEqual(pet.happy, 10 + 5 + 2.5)
        self.assertEqual(pet.hug(T0 + 30), "overloved")
        pet.hug(T0 + 30 + 601)  # after a break it's a full hug again
        self.assertEqual(pet.hug_streak, 0)
        self.assertEqual(pet.hugs, 5)

    def test_hug_works_while_asleep(self):
        self.assertEqual(Pet(asleep=True).hug(T0), "loved")

    def test_rates_and_next_stage(self):
        self.assertEqual(Pet().rate_per_hour("fullness"), -8)
        self.assertEqual(Pet(asleep=True).rate_per_hour("energy"), 20)
        self.assertEqual(Pet(poops=1).rate_per_hour("clean"), -14)
        pet = Pet(born=T0)
        self.assertEqual(pet.next_stage_in(T0), pet_state.EGG_SECONDS)
        self.assertIsNone(pet.next_stage_in(T0 + 10 * 24 * HOUR))

    def test_clean_and_heal(self):
        pet = Pet(clean=20, poops=2)
        self.assertEqual(pet.clean_up(), "cleaned")
        self.assertEqual((pet.clean, pet.poops), (100, 0))
        sick = Pet(sick=True, happy=50)
        self.assertEqual(sick.heal(), "healed")
        self.assertFalse(sick.sick)

    def test_mood_priority(self):
        self.assertEqual(Pet(asleep=True, fullness=0).mood(), "sleeping")
        self.assertEqual(Pet(fullness=10, clean=10).mood(), "hungry")
        self.assertEqual(Pet(fullness=90, happy=90, energy=90, clean=90).mood(), "happy")


class TestPersistence(unittest.TestCase):
    def test_save_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            pet_state.STATE_PATH = os.path.join(d, "sub", "state.json")
            self.assertIsNone(pet_state.load())
            pet = pet_state.new_pet("Bao")
            pet_state.save(pet)
            loaded = pet_state.load()
            self.assertEqual(loaded.name, "Bao")


if __name__ == "__main__":
    unittest.main()
