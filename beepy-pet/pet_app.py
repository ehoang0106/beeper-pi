#!/usr/bin/env python3
"""Beepy pet: a Tamagotchi-style friend for the Beepy's 50x13 screen and RGB LED.

Run `pet`. Keys: f feed · p play · s sleep/wake · c clean · h hug · m medicine ·
i stats · q quit. The pet keeps living (and getting hungry) while the game is closed.
"""

import curses
import locale
import os
import random
import signal
import sys
import time

import pet_art
import pet_copy
import pet_state
from pet_canvas import H, W, Canvas
from pet_led import Led
import pet_hilo_art
import pet_train_art
from pet_hilo_game import HiLoGame
from pet_minigame import Game
from pet_train_game import TrainGame
from pet_screens_main import draw_egg, draw_main, fmt_age
from pet_screens_hilo import draw_hilo
from pet_screens_menu import draw_menu
from pet_screens_other import draw_gone, draw_naming, draw_play, draw_stats
from pet_screens_train import draw_train

TICK = 0.5            # seconds per animation frame (memory LCD friendly)
ADVANCE_EVERY = 20    # ticks between stat decay updates (10 s)
SAVE_EVERY = 60       # ticks between autosaves (30 s)
STATUS_ROTATE = 16    # ticks before the status line picks a new message (8 s)
MESSAGE_TICKS = 6     # ticks an action message stays up (3 s)
ACTION_KEYS = set("fpschm")
NAME_CHARS = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -")
EFFECT_LEN = {"hatch": 7, "grow": 4, "wobble": 8}
HATCH_SEQ = [0, 1, 1, 2, 2, 3, 3]


class App:
    def __init__(self, pet):
        self.pet = pet
        self.led = Led()
        self.t = 0
        self.mode = "naming" if pet is None else "gone" if pet.ran_away else "main"
        self.effect_name, self.effect_start = None, 0
        self.message = None          # (glyph, text, until_tick)
        self.mood_msg = None         # (mood, glyph, text, since_tick)
        self.pending_key = None      # one key queued while an animation plays
        self.pressed = (None, -1)
        self.idle_dx, self.hop = 0, 0
        self.next_blink, self.next_hop, self.next_wander = 6, 14, 16
        self.love_until = -1
        self.name_buf, self.name_fresh = "Mochi", True
        self.game = Game()
        self.train = TrainGame(pet_train_art.GRID_W, pet_train_art.GRID_H)
        self.hilo = HiLoGame()
        self.prev_best = 0   # best score before this run, for the in-game NEW BEST badge
        self.result = None   # rewards shown on a game's end screen
        self.gone_since = 0
        self.last_stage = pet.stage() if pet else "egg"

    # --- what the screens ask for ----------------------------------------------
    def pressed_key(self):
        key, at = self.pressed
        return key if self.t - at < 1 else None

    def blinking(self):
        return self.t == self.next_blink - 1 and not self.effect_name and \
            self.pet.mood() not in ("sleeping", "sick")

    def status_line(self):
        if self.message and self.t < self.message[2]:
            return self.message[:2]
        mood = "egg" if self.pet.stage() == "egg" else self.pet.mood()
        if not self.mood_msg or self.mood_msg[0] != mood or self.t - self.mood_msg[3] >= STATUS_ROTATE:
            self.mood_msg = (mood, pet_copy.MOOD_GLYPH[mood], pet_copy.mood_line(mood, self.pet.name), self.t)
        return self.mood_msg[1:3]

    def face_and_particles(self, stage, x, y):
        if self.effect_name in pet_art.EFFECTS:
            face, parts = pet_art.EFFECTS[self.effect_name][self.t - self.effect_start]
            # Effect offsets were laid out on a 13-wide sprite: stretch them to this one.
            w = len(pet_art.TEMPLATES[stage][0])
            parts = [(dy, dx * w // 13, g) for dy, dx, g in parts]
            if self.effect_name == "feed" and face == "eat_a":
                mdx, mdy = pet_art.mouth_cell(stage)
                parts = [(mdy, mdx + 1, "▲")]
            return face, parts
        if self.effect_name == "grow":
            w = len(pet_art.TEMPLATES[stage][0])
            return "happy", [(-1, w - 2, "☼")]
        frame = (self.t // 2) % 2
        face = {
            "sleeping": ("sleeping", "snore")[frame],
            "sleepy": ("sleepy", "sleepy_b")[frame],
            "sad": ("sad", "sad_tear")[frame],
        }.get(self.pet.mood(), self.pet.mood())
        return (face if face in pet_art.FACES else "content"), []

    def egg_frame(self):
        if self.effect_name == "hatch":
            return pet_art.HATCH[HATCH_SEQ[self.t - self.effect_start]]
        wobbling = self.mode == "naming" or self.effect_name == "wobble" or self.t % 20 < 8
        return pet_art.egg_lean([0, -1, 0, 1][self.t % 4] if wobbling else 0)

    # --- events ------------------------------------------------------------------
    def say(self, glyph, text):
        self.message = (glyph, text, self.t + MESSAGE_TICKS)

    def say_result(self, result):
        self.say(*pet_copy.action_line(result, self.pet.name))

    def start_effect(self, name):
        self.effect_name, self.effect_start = name, self.t

    def tick(self):
        self.t += 1
        if self.effect_name:
            length = EFFECT_LEN.get(self.effect_name) or len(pet_art.EFFECTS[self.effect_name])
            if self.t - self.effect_start >= length:
                done, self.effect_name = self.effect_name, None
                if done == "hatch":
                    self.say_result("hatched")
                if self.pending_key:
                    key, self.pending_key = self.pending_key, None
                    self.on_key(key)
        if self.mode == "hilo" and self.hilo.step():
            self._finish("hilo")
        if self.mode == "play" and self.game.tick(self.t):
            self.pet.play_result(self.game.won())
            pet_state.save(self.pet)
        if self.pet and self.mode in ("main", "stats"):
            self._live_tick()
        self.led.set(self._led_mood(), self.t)
        self.led.tick(self.t)

    def _live_tick(self):
        pet = self.pet
        stage = pet.stage()
        if stage != self.last_stage:
            if self.last_stage == "egg":
                self.start_effect("hatch")
            else:
                self.start_effect("grow")
                self.say_result(stage)
            self.last_stage = stage
        if self.t % ADVANCE_EVERY == 0:
            poops = pet.poops
            pet.advance()
            if pet.poops > poops:
                self.say_result("poop")
            if pet.ran_away:
                self.mode, self.gone_since = "gone", self.t
                pet_state.save(pet)
        if self.t % SAVE_EVERY == 0:
            pet_state.save(pet)
        self._idle_motion()

    def _idle_motion(self):
        self.hop = 0
        if self.t >= self.next_blink:
            self.next_blink = self.t + random.randint(6, 10)
        calm = not self.effect_name and self.pet.mood() not in ("sleeping", "sick")
        if self.t >= self.next_hop:
            self.next_hop = self.t + random.randint(12, 20)
            self.hop = 1 if calm else 0
        if self.t >= self.next_wander:
            self.next_wander = self.t + random.randint(14, 18)
            if calm:
                self.idle_dx = max(-2, min(2, self.idle_dx + random.choice((-1, 1))))

    def _led_mood(self):
        if self.mode == "naming" or (self.pet and self.pet.stage() == "egg") or self.effect_name == "wobble":
            return "egg"
        if self.mode == "gone":
            return "gone"
        if self.effect_name in ("hatch", "grow"):
            return "flash"
        if self.mode == "play":
            if self.game.phase == "end":
                return "happy" if self.game.won() else "content"
            return "play"
        if self.mode in ("train", "hilo"):
            g = self.train if self.mode == "train" else self.hilo
            if g.phase == "end" and self.result:
                return "happy" if self.result["win"] else "content"
            return "play"
        if self.mode == "menu":
            return "play"
        if self.t < self.love_until and not self.pet.asleep:  # a tuck-in hug stays dark
            return "love"
        return self.pet.mood()

    # --- keys --------------------------------------------------------------------
    def on_key(self, key):
        """Returns False to quit."""
        handler = getattr(self, f"_key_{self.mode}")
        return handler(key) is not False

    def _key_naming(self, key):
        if key in ("\n", "\r"):
            gen = self.pet.generation + 1 if self.pet else 1
            self.pet = pet_state.new_pet(self.name_buf.strip() or "Mochi", gen)
            pet_state.save(self.pet)
            self.mode, self.last_stage = "main", "egg"
        elif key == "BACKSPACE":
            self.name_buf = "" if self.name_fresh else self.name_buf[:-1]
            self.name_fresh = False
        elif len(key) == 1 and key in NAME_CHARS:
            self.name_buf = key if self.name_fresh else (self.name_buf + key)[:8]
            self.name_fresh = False

    def _key_main(self, key):
        pet = self.pet
        if key == "q":
            return False
        if key == "i":
            self.mode = "stats"
            return
        if self.effect_name and key in ACTION_KEYS:
            self.pending_key = key
            return
        if key in ACTION_KEYS:
            self.pressed = (key, self.t)
        if pet.stage() == "egg":
            if key == "h":
                self.start_effect("wobble")
                self.say_result("pat")
            return
        if key == "f":
            result = pet.feed()
            self.start_effect("feed" if result == "ate" else "refuse")
        elif key == "p":
            result = pet.can_play()
            if result == "ok":
                self.mode = "menu"
                return
            self.start_effect("refuse")
        elif key == "s":
            result = pet.toggle_sleep()
            if result == "woke":
                self.start_effect("wake")
        elif key == "c":
            result = "asleep" if pet.asleep else pet.clean_up()
            if result == "cleaned":
                self.start_effect("clean")
        elif key == "h":
            result = pet.hug()
            self.start_effect("hug")
            self.love_until = self.t + 6
        elif key == "m":
            result = pet.heal()
        else:
            return
        self.say_result(result)
        pet_state.save(pet)

    def _key_play(self, key):
        g = self.game
        if g.phase == "intro":
            if key == "q":
                self.mode = "main"
            else:
                g.start(self.t)
        elif g.phase == "end":
            if key == "p" and self.pet.can_play() == "ok":
                g.start(self.t)
            else:
                self.mode = "main"
        elif key == "q":
            self.mode = "main"  # giving up costs nothing
        elif key in ("l", "r", "LEFT", "RIGHT"):
            g.guess({"LEFT": "l", "RIGHT": "r"}.get(key, key), self.t)

    def _key_menu(self, key):
        if key == "1":
            self.mode, self.game = "play", Game()
        elif key == "2":
            self.mode = "train"
            self.train = TrainGame(pet_train_art.GRID_W, pet_train_art.GRID_H)
        elif key == "3":
            self.mode, self.hilo = "hilo", HiLoGame()
        elif key == "q":
            self.mode = "main"

    def _start_run(self, game, best_field):
        self.prev_best, self.result = getattr(self.pet, best_field), None
        game.start()

    def _key_train(self, key):
        g = self.train
        if g.phase == "intro":
            if key == "q":
                self.mode = "menu"
            else:
                self._start_run(g, "best_train")
        elif g.phase == "playing":
            if key == "q":
                self.mode = "main"  # giving up costs nothing
            else:
                g.key(key)
        elif g.phase == "end":
            if key == "p" and self.pet.can_play() == "ok":
                self._start_run(g, "best_train")
            else:
                self.mode = "main"

    def _key_hilo(self, key):
        g = self.hilo
        if g.phase == "intro":
            if key == "q":
                self.mode = "menu"
            else:
                self._start_run(g, "best_streak")
        elif g.phase == "guess":
            if key == "q":
                self.mode = "main"
            else:
                g.key(key)
        elif g.phase == "reveal":
            if g.next():
                self._finish("hilo")
        elif g.phase == "end":
            if key == "p" and self.pet.can_play() == "ok":
                self._start_run(g, "best_streak")
            else:
                self.mode = "main"

    def train_frame(self):
        """One Sheep Train step (on the game's own timer, faster as the train grows)."""
        if self.mode == "train" and self.train.phase in ("playing", "crashed") and self.train.step():
            self._finish("train")

    def _finish(self, which):
        """Apply a finished run's rewards and remember them for the end screen."""
        art, score, field = ((pet_train_art, self.train.score, "best_train") if which == "train"
                             else (pet_hilo_art, self.hilo.streak, "best_streak"))
        happy, energy, win = next((h, e, w) for low, h, e, w in art.REWARDS if score >= low)
        new_best = score > self.prev_best
        happy += art.NEW_BEST_BONUS_HAPPY if new_best else 0
        self.pet.game_result(happy, energy, win, field, score)
        self.result = {"happy": happy, "energy": energy, "win": win, "new_best": new_best}
        pet_state.save(self.pet)

    def _key_stats(self, key):
        if key == "q":
            return False
        self.mode = "main"

    def _key_gone(self, key):
        if key == "q":
            return False
        if key == "n":
            self.mode, self.name_buf, self.name_fresh = "naming", "Mochi", True

    # --- drawing -----------------------------------------------------------------
    def draw(self, c):
        if self.mode == "main" and self.effect_name == "hatch":
            return draw_egg(c, self)
        {"naming": draw_naming, "main": draw_main, "play": draw_play, "menu": draw_menu,
         "train": draw_train, "hilo": draw_hilo, "stats": draw_stats, "gone": draw_gone}[self.mode](c, self)


def read_key(win):
    try:
        ch = win.get_wch()
    except curses.error:
        return None
    if ch in (curses.KEY_BACKSPACE, "\x7f", "\b"):
        return "BACKSPACE"
    arrows = {curses.KEY_LEFT: "LEFT", curses.KEY_RIGHT: "RIGHT", curses.KEY_UP: "UP", curses.KEY_DOWN: "DOWN"}
    if ch in arrows:  # the touchpad sends arrow keys
        return arrows[ch]
    if ch == curses.KEY_ENTER:
        return "\n"
    return ch if isinstance(ch, str) else None


def run(win):
    curses.curs_set(0)
    pet = pet_state.load()
    app = App(pet)
    if pet and not pet.ran_away:
        away = time.time() - pet_state_last_seen(pet)
        if away > 30 * 60:
            app.say(*pet_copy.welcome_back(pet.name, fmt_age(away)))
    next_tick = time.monotonic() + TICK
    next_frame = time.monotonic()
    try:
        while True:
            # Short input waits only while the train moves (steps every 0.15-0.30 s).
            win.timeout(30 if app.mode == "train" else 100)
            key = read_key(win)
            if key is not None and not app.on_key(key):
                break
            now = time.monotonic()
            if now >= next_tick:
                next_tick += TICK
                app.tick()
            if now >= next_frame:
                next_frame = now + app.train.step_seconds()
                app.train_frame()
            rows, cols = win.getmaxyx()
            if rows < H or cols < W:
                win.erase()
                win.addstr(0, 0, f"Need {W}x{H}, have {cols}x{rows}"[: max(1, cols - 1)])
            else:
                c = Canvas()
                app.draw(c)
                c.flush(win, (rows - H) // 2, (cols - W) // 2)
            win.noutrefresh()
            curses.doupdate()
    finally:
        app.led.off()
        if app.pet:
            pet_state.save(app.pet)


def pet_state_last_seen(pet):
    """When the game last saved, i.e. when the player was last here (before load's advance)."""
    try:
        return os.path.getmtime(pet_state.STATE_PATH)
    except OSError:
        return time.time()


def _exit_on_signal(*_):
    raise SystemExit


def main():
    if sys.argv[1:] == ["--status"]:
        import pet_status
        print(pet_status.summary())
        return
    locale.setlocale(locale.LC_ALL, "")
    if "utf" not in (locale.getlocale(locale.LC_CTYPE)[1] or "").lower():
        locale.setlocale(locale.LC_CTYPE, "C.UTF-8")
    os.environ.setdefault("ESCDELAY", "25")
    # Turn a kill / closed SSH session into a normal exit so the pet is saved and the LED goes off.
    for sig in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, _exit_on_signal)
    try:
        curses.wrapper(run)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
