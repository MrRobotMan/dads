import configparser
import json
import random
from collections import defaultdict
from typing import List, Tuple, Dict, Any, DefaultDict

from discord.ext import commands


def get_champs() -> Tuple[Dict[str, Dict[str, List[str]]], DefaultDict[str, List[str]]]:
    """
    Read in the data on the champions

    >>> get_champs() # doctest: +ELLIPSIS
    ({'Ahri': {'positions': ['Mid'], 'builds': []}, ...}, \
defaultdict(<class 'list'>, {'Mid': ['Ahri', ...], \
'Baron': ['Akali', ...], ...}))
    """
    with open("champs.json") as f:
        champs_data: Dict[str, Dict[str, List[str]]] = json.load(f)

    champ_positions: DefaultDict[str, List[str]] = defaultdict(list)

    for champ, attribs in champs_data.items():
        for pos in attribs["positions"]:
            champ_positions[pos].append(champ)

    return champs_data, champ_positions


def make_team(champ_positions: DefaultDict[str, List[str]]) -> List[str]:
    """
    Get a random team of 5 champs based on where they normally play.

    >>> random.seed(1)
    >>> make_team({'Mid': ['Aurelion Sol', 'Orianna'], \
'Baron': ['Darius', 'Riven'], \
'Support': ['Janna', 'Senna'], \
'Jungle': ['Evelynn', 'Rengar'], \
'Dragon': ['Lucian', 'Jinx']})
    ['Mid Aurelion Sol', 'Baron Darius', 'Support Senna', \
'Jungle Evelynn', 'Dragon Jinx']
    """
    team = []
    for position, champs in champ_positions.items():
        champ = random.choice(champs)
        # Uncomment below when AP / AD / Utility stuff is worked out
        # build = random.choice(champs_data[champ]['builds'])
        team.append(f"{position} {champ}")  # Add build once implemented
    return team


def make_chaos(champs: List[str]) -> List[str]:
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


def main() -> None:
    """
    The main bot. Has commands for team, teams, and chaos.
    """
    config = configparser.ConfigParser()
    config.read("env.ini")
    BOT_TOKEN = config["DISCORD"]["BOT_TOKEN"]

    champs_data, champ_positions = get_champs()

    bot = commands.Bot(command_prefix="!")

    @bot.command(name="team", help="Responds with a random team")
    async def on_message(ctx):
        """
        (1) 5 champ team with roles based on where they normally play
        """
        await ctx.send("\n".join(make_team(champ_positions)))

    @bot.command(name="teams", help="Responds with two random teams")
    async def on_message(ctx):
        """
        (2) 5 champ teams with roles based on where they normally play
        """
        response = ""
        for side in "AB":
            squad = "\n> ".join(make_team(champ_positions))
            response += f"Side {side}\n> {squad}\n"

        await ctx.send(response)

    @bot.command(
        name="chaos",
        help="Responds with two fully random teams (positions and damage type).",
    )
    async def on_message(ctx):
        """
        (2) 5 champ teams with roles and builds fully random
        """
        response = ""
        for side in "AB":
            squad = "\n> ".join(make_chaos(list(champs_data.keys())))
            response += f"Side {side}\n> {squad}\n"

        await ctx.send(response.strip())  # Remove tailing '\n'

    bot.run(BOT_TOKEN)


if __name__ == "__main__":
    """Proper way to note a module as can be run as a script"""
    main()
