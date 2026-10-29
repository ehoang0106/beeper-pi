"""Drive the Beepy RGB LED from the pet's mood (steady, blink or breathe).

Writes go to /sys/firmware/beepy; the `pi` user may write there because the keyboard
driver is loaded with sysfs_gid=<gpio>. Off the device (or without permission) the
LED silently does nothing, so the game still runs on a laptop for testing.
"""

SYSFS = "/sys/firmware/beepy"
BRIGHTNESS = 0.4  # the LED is harsh at full power, especially at night
SHOW_TICKS = 6    # show a mood for 3 s (500 ms ticks) after it appears, then go dark to save battery

# mood -> (rgb, behaviour); behaviours: steady, blink (1s), fast (0.5s), breathe
MOOD_LED = {
    "egg": ((255, 50, 0), "breathe"),
    "happy": ((0, 255, 80), "steady"),
    "content": ((0, 180, 160), "steady"),
    "love": ((255, 40, 140), "fast"),
    "hungry": ((255, 30, 0), "blink"),
    "sad": ((40, 60, 255), "steady"),
    "sleepy": ((130, 60, 220), "steady"),
    "sleeping": ((0, 0, 0), "steady"),  # lights out: no LED while it sleeps
    "dirty": ((200, 90, 0), "steady"),
    "sick": ((255, 0, 0), "fast"),
    "play": ((0, 220, 255), "steady"),
    "flash": ((255, 255, 255), "fast"),
    "gone": ((0, 0, 0), "steady"),
}


class Led:
    def __init__(self):
        self.mood = None
        self.show_until = 0  # tick after which the LED goes dark until the mood changes
        self.last = None  # last written (r, g, b, on), to skip redundant writes
        self.ok = True

    def set(self, mood, t):
        """Show `mood`; a new mood (or the first one) lights the LED for SHOW_TICKS."""
        if mood != self.mood:
            self.mood, self.show_until = mood, t + SHOW_TICKS

    def tick(self, t):
        """Call every 500 ms tick with a running tick counter."""
        if self.mood is None:
            return
        if t >= self.show_until:
            self._write((0, 0, 0), False)
            return
        rgb, mode = MOOD_LED[self.mood]
        on, scale = True, BRIGHTNESS
        if mode == "blink":
            on = (t // 2) % 2 == 0
        elif mode == "fast":
            on = t % 2 == 0
        elif mode == "breathe":
            scale = BRIGHTNESS if (t // 2) % 2 == 0 else BRIGHTNESS * 0.3
        color = tuple(round(c * scale) for c in rgb)
        self._write(color, on and any(color))

    def off(self):
        self._write((0, 0, 0), False)

    def _write(self, color, on):
        state = (*color, on)
        if not self.ok or state == self.last:
            return
        try:
            if on:
                for name, level in zip(("led_red", "led_green", "led_blue"), color):
                    with open(f"{SYSFS}/{name}", "w") as f:
                        f.write(str(level))
            with open(f"{SYSFS}/led", "w") as f:
                f.write("1" if on else "0")
            self.last = state
        except OSError:
            self.ok = False  # not on a Beepy, or no permission: run without the LED
