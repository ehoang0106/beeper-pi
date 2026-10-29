"""Headless render tests: every screen and animation frame fits 50x13 and uses only
glyphs the Beepy console font can draw. `python3 test_pet_render.py show` prints them.
"""

import sys
import time
import types
import unittest

import pet_art
import pet_canvas
import pet_state
from pet_app import App
from pet_canvas import Canvas

SAFE = set(
    " !\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`"
    "abcdefghijklmnopqrstuvwxyz{|}~"
    "─│┌┐└┘├┤┬┴┼═║╔╗╚╝╠╣╦╩╬╥"
    "█▀▄▌▐░▒▓■▪"
    "☺☻♥♦♣♠•◘○◙♂♀♪♫☼►◄↕‼¶§▬↨↑↓→←∟↔▲▼·°∙√ⁿ²≈±≥≤÷Ωε∩≡φαβπΣσµτΦΘδ∞"
)

NOW = time.time()
HOUR = 3600


class StrictCanvas(Canvas):
    """Fails instead of clipping, so overflowing text can't hide."""

    def text(self, row, col, s, attr=0):
        assert 0 <= row < pet_canvas.H, f"row {row} off screen: {s!r}"
        assert col >= 0 and col + len(s) <= pet_canvas.W, f"row {row} col {col}: {s!r} overflows"
        super().text(row, col, s, attr)


def make_app(age_hours=30, mode="main", **stats):
    pet = pet_state.Pet(name="Mochi", born=NOW - age_hours * HOUR, updated=NOW, **stats)
    app = App(pet)
    app.mode = mode
    app.last_stage = pet.stage()
    return app


def render(app):
    c = StrictCanvas()
    app.draw(c)
    return c


def _frozen(app):
    """Render now and keep the result, so later game steps don't change it."""
    c = StrictCanvas()
    app.draw(c)
    return types.SimpleNamespace(draw=lambda canvas, cells=c.cells: canvas.cells.__init__(cells))


def train_scenarios():
    """A real Sheep Train run: steer toward lambs, then into the fence; every frame."""
    import random as _r
    out = []
    app = make_app(age_hours=100, mode="train", best_train=5)
    app.train.rng = _r.Random(3)
    out.append(("train intro", _frozen(app)))
    app._start_run(app.train, "best_train")
    g = app.train
    for i in range(400):
        if g.phase == "playing" and g.lamb:  # greedy steering toward the lamb
            (hx, hy), (lx, ly) = g.train[0], g.lamb
            want = "d" if lx > hx else "a" if lx < hx else "s" if ly > hy else "w"
            if i > 300:
                want = "w"  # eventually drive into the top fence
            g.key(want)
        app.t = i
        out.append((f"train f{i} {g.phase}", _frozen(app)))
        if g.step():
            app._finish("train")
            break
    out.append(("train end", _frozen(app)))
    return out


def hilo_scenarios():
    import random as _r
    out = []
    app = make_app(age_hours=2, mode="hilo", best_streak=3)
    app.hilo.rng = _r.Random(8)
    out.append(("hilo intro", _frozen(app)))
    app._start_run(app.hilo, "best_streak")
    g = app.hilo
    deals = [("7", "♣"), ("Q", "♥"), ("Q", "♠"), ("10", "♦"), ("2", "♣"), ("K", "♠"), ("A", "♠")]
    g.current, g.deck = deals[0], list(reversed(deals[1:]))
    for key in ["h", "l", "l", "l", "h", "h"]:
        out.append((f"hilo guess {g.streak}", _frozen(app)))
        g.key(key)
        out.append((f"hilo reveal {g.result} {g.next_card[0]}", _frozen(app)))
        if g.next():
            app._finish("hilo")
            break
    out.append(("hilo end", _frozen(app)))
    return out


def scenarios():
    """(title, app) pairs covering every screen, mood and animation frame."""
    out = []
    egg = make_app(age_hours=0.02)
    out.append(("egg", egg))
    naming = App(None)
    out.append(("naming", naming))
    for stage, age in (("baby", 2), ("teen", 30), ("adult", 100)):
        for mood, stats in {
            "content": {}, "happy": dict(fullness=90, happy=90, energy=90, clean=90),
            "hungry+poop": dict(fullness=18, poops=1), "sad": dict(happy=10),
            "sleepy": dict(energy=10), "sleeping": dict(asleep=True, asleep_since=NOW - 2 * HOUR),
            "dirty": dict(clean=5, poops=2), "sick": dict(sick=True, fullness=5),
        }.items():
            out.append((f"{stage} {mood}", make_app(age_hours=age, **stats)))
        for effect, n in [(e, len(f)) for e, f in pet_art.EFFECTS.items()] + [("grow", 4)]:
            for i in range(n):
                app = make_app(age_hours=age)
                app.effect_name, app.effect_start, app.t = effect, 0, i
                out.append((f"{stage} {effect} {i}", app))
    hatch = make_app(age_hours=0.1)
    for i in range(7):
        h = make_app(age_hours=0.1)
        h.effect_name, h.effect_start, h.t = "hatch", 0, i
        out.append((f"hatch {i}", h))
    for phase in ("intro", "shuffle", "guess", "reveal", "end-win", "end-lose"):
        app = make_app(age_hours=100, mode="play")
        g = app.game
        if phase != "intro":
            g.start(0)
            g.round = 3
            g.results = [True, False]
        if phase in ("guess", "reveal"):
            g.phase = "guess"
            g.guess("r", 0)
            if phase == "guess":
                g.phase = "guess"
        if phase.startswith("end"):
            g.phase, g.results = "end", [True, True, False, True, False] if phase == "end-win" else [False, True, False, False, False]
        out.append((f"play {phase}", app))
    out.append(("menu new", make_app(age_hours=100, mode="menu")))
    out.append(("menu bests", make_app(age_hours=100, mode="menu", best_train=23, best_streak=9)))
    out += train_scenarios() + hilo_scenarios()
    out.append(("stats", make_app(age_hours=100, mode="stats", meals=42, hugs=118, games=14, wins=9)))
    gone = make_app(age_hours=150, mode="gone", ran_away=True, fullness=0, meals=42, hugs=118)
    gone.t, gone.gone_since = 10, 0
    out.append(("gone", gone))
    return out


class TestRender(unittest.TestCase):
    def test_every_screen_fits_and_uses_safe_glyphs(self):
        for title, app in scenarios():
            with self.subTest(title):
                c = render(app)
                bad = {ch for line in c.lines() for ch in line} - SAFE
                self.assertFalse(bad, f"{title}: unsafe glyphs {bad}")

    def test_copy_fits_with_longest_name(self):
        import pet_copy
        lines = [l for ls in pet_copy.MOOD_LINES.values() for l in ls]
        lines += [l for _, ls in pet_copy.ACTION_LINES.values() for l in ls]
        for line in lines:
            text = line.format(n="ABCDEFGH")
            self.assertLessEqual(len(text), 46, text)
            self.assertFalse(set(text) - SAFE, text)


if __name__ == "__main__":
    if sys.argv[1:] == ["show"]:
        for title, app in scenarios():
            print(f"=== {title}")
            for line in render(app).lines():
                print(line + "|")
    else:
        unittest.main()
