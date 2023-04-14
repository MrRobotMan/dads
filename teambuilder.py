"""
Functions to create random teams.
"""

import json
import random
from collections import defaultdict
from typing import DefaultDict

from paths import CHAMPS


def get_champs() -> tuple[list[str], DefaultDict[str, list[str]]]:
    """
    Read in the data on the champions

    >>> get_champs() # doctest: +ELLIPSIS
    ({'Ahri': ['Mid'], ...}, \
DefaultDict(<class 'list'>, {'Mid': ['Ahri', ...], \
'Baron': ['Akali', ...], ...}))
    """
    with CHAMPS.open("r") as json_file:
        champs_data: dict[str, list[str]] = json.load(json_file)

    champ_positions: DefaultDict[str, list[str]] = defaultdict(list)

    for champ, positions in champs_data.items():
        for pos in positions:
            champ_positions[pos].append(champ)

    return list(champs_data.keys()), champ_positions


def make_team(champ_positions: DefaultDict[str, list[str]]) -> list[str]:
    """
    Get a random team of 5 champs based on where they normally play.

    >>> random.seed(1)
    >>> make_team({'Mid': ['Aurelion Sol', 'Oriana'], \
'Baron': ['Darius', 'Riven'], \
'Support': ['Janna', 'Senna'], \
'Jungle': ['Evelynn', 'Rengar'], \
'Dragon': ['Lucian', 'Jinx']})
    ['Mid Aurelion Sol', 'Baron Darius', 'Support Senna', \
'Jungle Evelynn', 'Dragon Jinx']
    """
    team: list[str] = []
    for position, champs in champ_positions.items():
        champ = random.choice(champs)
        # Uncomment below when AP / AD / Utility stuff is worked out
        # build = random.choice(champs_data[champ]['builds'])
        team.append(f"{position} {champ}")  # Add build once implemented
    random.shuffle(team)
    return team


def make_chaos(champs: list[str]) -> list[str]:
    """
    Get a fully random ream of 5 champs. They will get randomly assigned
    to AD / AP / Tank as well as positions.

    >>> random.seed(1)
    >>> make_chaos(['Aurelion Sol', 'Darius', 'Janna', 'Evelynn', 'Lucian', \
'Ezreal', 'Blitzcrank', 'Kennen', 'Draven', 'Varus'])
    ['AP Baron Janna', 'AP Dragon Darius', 'Tank Mid Lucian', \
'AP Jungle Aurelion Sol', 'AD Support Evelynn']
    """
    positions = ["Baron", "Dragon", "Mid", "Jungle", "Support"]
    build_opts = ["AD", "AP", "Tank"]
    team = random.sample(champs, 5)
    builds = [random.choice(build_opts) for _ in positions]
    return [f"{builds[i]} {positions[i]} {champ}" for i, champ in enumerate(team)]
