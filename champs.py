import argparse
import json
from collections import OrderedDict


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-n", "--new", action="store_true", default=False, help="Add a new champ"
    )
    args = parser.parse_args()
    if args.new:
        champ = input("Enter the champ's name: ")
        positions = input("Enter the champ's positions (b, m, d, s, j): ")
        roles = {"b": "Baron", "m": "Mid", "d": "Dragon", "s": "Support", "j": "Jungle"}
        # builds = input("Enter the champ's builds: ")
        new_champ = {champ: {"positions": [roles[i] for i in positions], "builds": []}}
    with open("champs.json", "r") as fs:
        unordered_champs: dict[str, dict[str, list[str]]] = json.load(fs)
        if args.new:
            unordered_champs.update(new_champ)
        champs = OrderedDict(sorted(unordered_champs.items()))
    with open("champs.json", "w") as fp:
        json.dump(champs, fp, indent=2)


if __name__ == "__main__":
    main()
