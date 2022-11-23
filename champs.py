"""
Helper module to add new champs to the pool.
"""

import json
from collections import OrderedDict
from pathlib import Path

CHAMPS = Path("champs.json")


def main() -> None:
    """Add new champs. Enter a blank to exit."""
    with CHAMPS.open(encoding="utf-8") as json_file:
        unordered_champs: dict[str, list[str]] = json.load(json_file)
    while champ := input("Enter the champ's name (enter blank to exit): "):
        positions = input("Enter the champ's positions (b, m, d, s, j): ")
        roles = {"b": "Baron", "m": "Mid", "d": "Dragon", "s": "Support", "j": "Jungle"}
        # builds = input("Enter the champ's builds: ")
        # new_champ = {champ: {"positions": [roles[i] for i in positions], "builds": []}}
        new_champ = {champ: [roles[i] for i in sorted(positions)]}
        unordered_champs.update(new_champ)
    champs = OrderedDict(sorted(unordered_champs.items()))
    with CHAMPS.open("w", encoding="utf-8") as json_file:
        json.dump(champs, json_file, indent=2)


if __name__ == "__main__":
    main()
