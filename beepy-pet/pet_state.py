"""Beepy pet: game state, real-time decay, moods and actions (no UI here).

Stats are 0-100 and decay with wall-clock time, so the pet keeps living while the
game is closed. Nothing runs in the background to do that: state stores the time
it was last updated and `advance()` replays the elapsed hours whenever it's loaded.
"""

import json
import os
import random
import time
from dataclasses import asdict, dataclass, field

STATE_PATH = os.path.expanduser("~/.local/share/beepy-pet/state.json")

HOUR = 3600
EGG_SECONDS = 5 * 60          # hatches after 5 minutes
BABY_SECONDS = 1 * 24 * HOUR  # baby for the first day
TEEN_SECONDS = 3 * 24 * HOUR  # teen until day 3, adult after
RUNAWAY_NEGLECT_HOURS = 48    # hours with 2+ stats at zero before it leaves
SICK_NEGLECT_HOURS = 6        # hours with any stat at zero before it gets sick

# Points lost per hour: (awake, asleep). Fullness 100 -> 0 in ~12h awake.
DECAY = {
    "fullness": (8, 3),
    "happy": (6, 1),
    "energy": (5, -20),  # negative = sleeping restores energy
    "clean": (4, 1),
}
POOP_CHANCE_PER_HOUR = 0.25   # while awake
POOP_CLEAN_PENALTY = 10       # extra clean loss per hour per poop on the floor
HUG_GAIN = 10                 # happiness from a hug after a break
HUG_STREAK_SECONDS = 600      # hugs closer together than this give half as much each time
STATS = ("fullness", "happy", "energy", "clean")


@dataclass
class Pet:
    name: str = "Mochi"
    born: float = field(default_factory=time.time)
    updated: float = field(default_factory=time.time)
    fullness: float = 80
    happy: float = 80
    energy: float = 80
    clean: float = 100
    asleep: bool = False
    asleep_since: float = 0
    poops: int = 0
    sick: bool = False
    zero_hours: float = 0     # consecutive hours with any stat at zero
    neglect_hours: float = 0  # consecutive hours with 2+ stats at zero
    ran_away: bool = False
    generation: int = 1
    # Lifetime counters shown on the stats screen.
    meals: int = 0
    hugs: int = 0
    games: int = 0
    wins: int = 0
    cleans: int = 0
    naps: int = 0
    last_hug: float = 0
    best_train: int = 0   # Sheep Train: most lambs collected
    best_streak: int = 0  # Higher or Lower: longest streak
    hug_streak: int = 0

    # --- derived -------------------------------------------------------------
    def age_seconds(self, now=None):
        return (now or time.time()) - self.born

    def stage(self, now=None):
        age = self.age_seconds(now)
        if age < EGG_SECONDS:
            return "egg"
        if age < BABY_SECONDS:
            return "baby"
        if age < TEEN_SECONDS:
            return "teen"
        return "adult"

    def mood(self):
        """Single most important mood, used to pick sprite, LED and status text."""
        if self.ran_away:
            return "gone"
        if self.asleep:
            return "sleeping"
        if self.sick:
            return "sick"
        if self.fullness < 25:
            return "hungry"
        if self.clean < 25 or self.poops >= 2:
            return "dirty"
        if self.energy < 20:
            return "sleepy"
        if self.happy < 30:
            return "sad"
        if min(self.fullness, self.happy, self.energy, self.clean) >= 70:
            return "happy"
        return "content"

    def needs(self):
        """Stats in trouble, most urgent first, for warning badges and notifications."""
        out = []
        if self.sick:
            out.append("sick")
        for stat, label in (("fullness", "hungry"), ("happy", "lonely"), ("energy", "tired"), ("clean", "dirty")):
            if getattr(self, stat) < 25:
                out.append(label)
        if self.poops and "dirty" not in out:
            out.append("dirty")
        return out

    def asleep_for(self, now=None):
        return (now or time.time()) - self.asleep_since if self.asleep else 0

    def runaway_reason(self):
        return "dirty" if self.clean <= 0 and self.fullness > 0 else "hungry"

    def next_stage_in(self, now=None):
        """Seconds until the next stage, or None when fully grown."""
        age = self.age_seconds(now)
        for limit in (EGG_SECONDS, BABY_SECONDS, TEEN_SECONDS):
            if age < limit:
                return limit - age
        return None

    def rate_per_hour(self, stat):
        """Current change per hour for a stat (positive = rising), for the stats screen."""
        per_hour = -DECAY[stat][1 if self.asleep else 0]
        if stat == "clean":
            per_hour -= self.poops * POOP_CLEAN_PENALTY
        if self.sick and stat != "energy":
            per_hour *= 1.5
        return per_hour

    # --- time ----------------------------------------------------------------
    def advance(self, now=None, rng=random):
        """Apply decay for the time since `updated`, one hour-sized step at a time."""
        now = now or time.time()
        if self.ran_away or self.stage(now) == "egg":
            self.updated = now
            return
        # Eggs don't decay: start the clock at hatch time if we were still an egg.
        start = max(self.updated, self.born + EGG_SECONDS)
        remaining = max(0.0, now - start)
        while remaining > 0:
            step = min(remaining, HOUR)
            self._decay(step / HOUR, rng)
            remaining -= step
        self.updated = now

    def _decay(self, hours, rng):
        idx = 1 if self.asleep else 0
        for stat in STATS:
            loss = DECAY[stat][idx] * hours
            if stat == "clean":
                loss += self.poops * POOP_CLEAN_PENALTY * hours
            if self.sick and stat != "energy":
                loss *= 1.5
            setattr(self, stat, _clamp(getattr(self, stat) - loss))
        if not self.asleep and rng.random() < POOP_CHANCE_PER_HOUR * hours:
            self.poops = min(self.poops + 1, 3)
        if self.asleep and self.energy >= 100:
            self.asleep = False  # wakes up on its own when rested

        zeros = sum(getattr(self, s) <= 0 for s in STATS)
        self.zero_hours = self.zero_hours + hours if zeros else 0
        self.neglect_hours = self.neglect_hours + hours if zeros >= 2 else 0
        if self.zero_hours >= SICK_NEGLECT_HOURS:
            self.sick = True
        if self.neglect_hours >= RUNAWAY_NEGLECT_HOURS:
            self.ran_away = True

    # --- actions (return a short result key the UI turns into feedback) -------
    def feed(self):
        if self.asleep:
            return "asleep"
        if self.fullness >= 95:
            return "full"
        self.fullness = _clamp(self.fullness + 30)
        self.energy = _clamp(self.energy + 5)
        self.meals += 1
        return "ate"

    def play_result(self, won):
        """Called after the mini-game. Playing is fun even when you lose."""
        self.happy = _clamp(self.happy + (20 if won else 5))
        self.energy = _clamp(self.energy - 10)
        self.games += 1
        self.wins += won
        return "won" if won else "lost"

    def game_result(self, happy, energy, won, best_field=None, score=0):
        """Apply a mini-game's rewards; returns True if `score` is a new best."""
        self.happy = _clamp(self.happy + happy)
        self.energy = _clamp(self.energy + energy)
        self.games += 1
        self.wins += bool(won)
        if best_field and score > getattr(self, best_field):
            setattr(self, best_field, score)
            return True
        return False

    def can_play(self):
        if self.asleep:
            return "asleep"
        if self.energy < 15:
            return "tired"
        return "ok"

    def toggle_sleep(self):
        self.asleep = not self.asleep
        if self.asleep:
            self.naps += 1
            self.asleep_since = time.time()
        return "slept" if self.asleep else "woke"

    def clean_up(self):
        if self.poops == 0 and self.clean >= 95:
            return "spotless"
        self.poops = 0
        self.clean = 100
        self.cleans += 1
        return "cleaned"

    def hug(self, now=None):
        """Hugs work while asleep (a tuck-in). Back-to-back hugs give less and less."""
        now = now or time.time()
        self.hug_streak = self.hug_streak + 1 if now - self.last_hug < HUG_STREAK_SECONDS else 0
        self.last_hug = now
        gain = HUG_GAIN / (2 ** self.hug_streak)
        self.happy = _clamp(self.happy + gain)
        self.hugs += 1
        return "loved" if gain >= 2 else "overloved"

    def heal(self):
        """Medicine: only needed when sick, costs some happiness (it tastes bad)."""
        if not self.sick:
            return "healthy"
        self.sick = False
        self.zero_hours = 0
        self.happy = _clamp(self.happy - 10)
        return "healed"


def _clamp(v):
    return max(0.0, min(100.0, v))


def load():
    """Load the pet and bring it up to date, or None if there is no pet yet."""
    try:
        with open(STATE_PATH) as f:
            pet = Pet(**json.load(f))
    except FileNotFoundError:
        return None
    pet.advance()
    return pet


def save(pet):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(asdict(pet), f, indent=1)
    os.replace(tmp, STATE_PATH)  # atomic, so a crash never leaves a half-written save


def new_pet(name, generation=1):
    return Pet(name=name, generation=generation)
