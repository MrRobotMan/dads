"""
Paths for commonly needed files.
"""

from pathlib import Path

PROJ_PATH = Path(__file__).parent
TIMEOUTS = PROJ_PATH / "timeouts.json"
MIST = PROJ_PATH / "mistborn.json"
CHAMPS = PROJ_PATH / "champs.json"
INI = PROJ_PATH / "env.ini"
GAMES = PROJ_PATH / "games.json"
NAMES = PROJ_PATH / "names.json"
