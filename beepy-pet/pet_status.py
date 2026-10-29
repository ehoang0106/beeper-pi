"""One-line pet summary for other tools (the `home` screen): `pet --status`.

Prints tab-separated fields, brought up to date like the game does on load:
  name stage age mood glyph fullness happy energy clean need asleep hatch_min
`need` is the most urgent badge (SICK HUNGRY TIRED DIRTY SAD POOP) or "-".
With no pet yet it prints just "none". Read-only: never writes the save file.
"""

import json

import pet_copy
import pet_state
from pet_screens_main import badges, fmt_age


def summary():
    try:
        with open(pet_state.STATE_PATH) as f:
            pet = pet_state.Pet(**json.load(f))
    except FileNotFoundError:
        return "none"
    pet.advance()
    stage = pet.stage()
    mood = "egg" if stage == "egg" and not pet.ran_away else pet.mood()
    found = badges(pet)
    hatch = round((pet.next_stage_in() or 0) / 60) if stage == "egg" else 0
    fields = [pet.name, stage.upper(), fmt_age(pet.age_seconds()), mood,
              pet_copy.MOOD_GLYPH.get(mood, "·"),
              *(str(round(getattr(pet, s))) for s in pet_state.STATS),
              found[0][0] if found else "-", "1" if pet.asleep else "0", str(hatch)]
    return "\t".join(fields)


if __name__ == "__main__":
    print(summary())
