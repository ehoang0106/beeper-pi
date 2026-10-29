"""Beepy pet micro-copy. `{n}` is the pet's name (max 8 chars); every line fits 46 columns."""

import random

# Status line glyph per mood (drawn bold at row 10, col 1).
MOOD_GLYPH = {
    "happy": "☻", "content": "☺", "hungry": "○", "sad": "▼", "sleepy": "z",
    "sleeping": "Z", "dirty": "≈", "sick": "+", "love": "♥", "egg": "○", "play": "♪",
}

MOOD_LINES = {
    "happy": ["{n} is bouncing off the walls!", "{n} wiggles happily. ♪",
              "Best day ever, says {n}.", "{n} does a tiny victory dance."],
    "content": ["{n} is humming a little song.", "{n} watches the clouds go by.",
                "All good. {n} blinks at you.", "{n} is just vibing."],
    "hungry": ["{n}'s tummy is rumbling...", "{n} is eyeing your snacks. [f]",
               "{n} dreams of rice balls ▲", "Feed me? {n} looks hopeful."],
    "sad": ["{n} misses you. A hug? [h]", "{n} sighs at the window.",
            "{n} wants someone to play with.", "Kinda quiet in here..."],
    "sleepy": ["{n} is yawning big yawns.", "{n} rubs their eyes. Bed? [s]",
               "Eyelids getting heavy...", "{n} nods off mid-blink."],
    "sleeping": ["Shh... {n} is dreaming.", "zzz... {n} snores softly.",
                 "{n} dreams of flying rice balls."],
    "dirty": ["{n} is a little stinky. [c]", "Flies are visiting {n}...",
              "Bath time? {n} is smudgy.", "Uh oh. Somebody pooped. [c]"],
    "sick": ["{n} feels wobbly. Medicine? [m]", "{n} has the sniffles... [m]",
             "{n} isn't well. Try medicine [m]"],
    "love": ["{n} loves you this much! ♥", "♥ ♥ ♥  {n} melts into the hug.",
             "{n} snuggles in. So warm."],
    "egg": ["Something is wiggling inside...", "The egg feels warm.",
            "Tap tap... was that a heartbeat?"],
}

# Result keys returned by pet_state actions -> (glyph, lines)
ACTION_LINES = {
    "ate": ("♥", ["Nom nom nom! ▲", "{n} licks the plate clean."]),
    "full": ("☺", ["{n} is stuffed! Maybe later."]),
    "cleaned": ("√", ["Squeaky clean! √", "Sparkly! {n} smells like soap."]),
    "spotless": ("√", ["Already sparkling clean! √"]),
    "slept": ("Z", ["Lights out. Sweet dreams, {n}."]),
    "woke": ("☼", ["Good morning, {n}! ☼"]),
    "asleep": ("Z", ["Shh, {n} is asleep. [s] wakes"]),
    "tired": ("z", ["{n} is too sleepy to play."]),
    "loved": ("♥", MOOD_LINES["love"]),
    "overloved": ("♥", ["{n} is already super loved!"]),
    "healed": ("+", ["Yuck medicine! But {n} feels better."]),
    "healthy": ("☺", ["{n} isn't sick. No medicine needed."]),
    "poop": ("≈", ["Oops. {n} made a little mess."]),
    "hatched": ("☼", ["{n} says hello, world!"]),
    "teen": ("☼", ["{n} grew up! Now a TEEN."]),
    "adult": ("☼", ["{n} is all grown up! ADULT."]),
    "pat": ("○", MOOD_LINES["egg"]),
}

GRANDMA_NOTE = {
    "hungry": "I got hungry and a bit lonely, so I",
    "dirty": "My room got too messy, so I",
}


def mood_line(mood, name):
    return random.choice(MOOD_LINES[mood]).format(n=name)


def action_line(result, name):
    glyph, lines = ACTION_LINES[result]
    return glyph, random.choice(lines).format(n=name)


def welcome_back(name, away):
    return "☻", f"{name} missed you! Away {away}."
