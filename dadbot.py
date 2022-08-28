import configparser
import datetime as dt
import json
import logging
import random
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, DefaultDict, Iterator, Optional

import discord
from discord.ext import commands

PROJ_PATH = Path(__file__).parent
TIMEOUTS = PROJ_PATH / "timeouts.json"
MIST = PROJ_PATH / "mistborn.json"
CHAMPS = PROJ_PATH / "champs.json"
INI = PROJ_PATH / "env.ini"
TIMEOUT = dict[str, tuple[int, int, str | bool, int]]

handler = logging.FileHandler(
    filename=PROJ_PATH / "discord.log", encoding="utf-8", mode="w"
)
logger = logging.getLogger("debug")
logger.setLevel(logging.DEBUG)
logger.addHandler(
    logging.FileHandler(filename=PROJ_PATH / "debug.log", encoding="utf-8", mode="w")
)


def get_champs() -> tuple[list[str], DefaultDict[str, list[str]]]:
    """
    Read in the data on the champions

    >>> get_champs() # doctest: +ELLIPSIS
    ({'Ahri': ['Mid'], ...}, \
DefaultDict(<class 'list'>, {'Mid': ['Ahri', ...], \
'Baron': ['Akali', ...], ...}))
    """
    with CHAMPS.open() as f:
        champs_data: dict[str, list[str]] = json.load(f)

    champ_positions: DefaultDict[str, list[str]] = defaultdict(list)

    for champ, positions in champs_data.items():
        for pos in positions:
            champ_positions[pos].append(champ)

    return list(champs_data.keys()), champ_positions


def make_team(champ_positions: DefaultDict[str, list[str]]) -> list[str]:
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
    team: list[str] = []
    for position, champs in champ_positions.items():
        champ = random.choice(champs)
        # Uncomment below when AP / AD / Utility stuff is worked out
        # build = random.choice(champs_data[champ]['builds'])
        team.append(f"{position} {champ}")  # Add build once implemented
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


def get_user_timeout_data(
    time: dt.datetime, data: tuple[int, int, str | bool, int]
) -> tuple[int, int]:
    """Checks if the indicated user is in timeout

    Args:
        time (dt.datetime): Time of the current check
        data (tuple[int, int, str | bool, int]): Timeout data
    Returns:
        tuple[int, int]: Number of times in timeout and duration (seconds)
    """
    if isinstance(data[2], bool):
        # Not in timeout.
        return (data[0], data[1])
    latest_in_timeout = dt.datetime.strptime(data[2], "%Y-%m-%d, %H:%M:%S")
    return (data[0], data[1] + int((time - latest_in_timeout).total_seconds()))


def seconds_to_hms(total_seconds: float) -> str:
    """Convert seconds to H:M:S

    Args:
        total_seconds (int): Total number of seconds

    Returns:
        str: hours:minutes:seconds
    >>> seconds_to_hms(4340)
    '1:12:20'
    """
    hours, minutes = divmod(total_seconds, 3600)
    minutes, seconds = divmod(minutes, 60)
    return f"{hours}:{minutes}:{seconds}"


def get_timeout_leaderboard(
    time: dt.datetime, data: TIMEOUT
) -> tuple[Iterator[tuple[int, int]], ...]:
    """Return the most timed out people.

    Args:
        time (dt.datetime): Time of the current check
        data (dict[str, tuple[int, int, str | bool, int]]): Timeout data

    Returns:
        tuple[list[tuple[int, int]], list[tuple[int, int]]]: users and number of timeouts / total time.
    """
    logger.debug(data)
    compiled = {
        (*get_user_timeout_data(time, v), idx): v[3]
        for idx, v in enumerate(data.values())
    }
    logger.debug(compiled)
    most_timed_out = sorted(list(compiled.items()), key=lambda x: x[0][0])[:3]
    longest_timed_out = sorted(list(compiled.items()), key=lambda x: x[0][1])[:3]
    # most_timed_out = "\n".join(
    #     f"{idx}: | {user[0][0]} | {user[1]}"
    #     for idx, user in enumerate(timed_out_qty)
    # )
    # longest_timed_out = "\n".join(
    #     f"{idx}: | {seconds_to_hms(user[0][1])} | {user[1]}"
    #     for idx, user in enumerate(timed_out_time)
    # )
    return (
        ((user[0][0], user[1]) for user in most_timed_out),
        ((user[0][1], user[1]) for user in longest_timed_out),
    )


async def entered_timeout(user: discord.Member, time: dt.datetime) -> None:
    """Record the timeout into the log.

    Args:
        user (discord.Member): User in timeout
        time (dt.datetime): Time of timeout
    """
    with TIMEOUTS.open() as fs:
        data: TIMEOUT = json.load(fs)
    existing = data.setdefault(user.name, (0, 0, True, user.id))
    number_of_timeouts = existing[0] + 1
    data[user.name] = (
        number_of_timeouts,
        existing[1],
        time.strftime("%Y-%m-%d, %H:%M:%S"),
        user.id,
    )
    with TIMEOUTS.open("w+") as fs:
        json.dump(data, fs, indent=2)


async def left_timeout(user: discord.Member, time: dt.datetime) -> None:
    """Record the timeout into the log.

    Args:
        user (discord.Member): User no longer in timeout
        time (dt.datetime): Time of timeout ending
    """
    with TIMEOUTS.open() as fs:
        data: TIMEOUT = json.load(fs)
    existing = data.setdefault(user.name, (0, 0, False, user.id))
    duration = existing[1]
    if isinstance(existing[2], bool):
        logger.error(f"{user.display_name} left timeout when not in it.")
    else:
        last_put_in_timeout = dt.datetime.strptime(existing[2], "%Y-%m-%d, %H:%M:%S")
        duration += (time - last_put_in_timeout).total_seconds()
    data[user.name] = (
        existing[0],
        int(duration),
        False,
        user.id,
    )
    with TIMEOUTS.open("w+") as fs:
        json.dump(data, fs, indent=2)


def message_pyn() -> Iterator[str]:
    """Ping PYN every hour on Thursdays until he posts the announcement.

    Returns:
        str: Message to PYN
    """
    messages = (
        "Thursday",
        "Did you know it's Thursday?",
        "Still no Thursday announcement...",
        "Hello? Thursday",
    )
    message_index = 0
    while True:
        yield messages[message_index]
        message_index += 1
        message_index %= len(messages)


def next_week() -> float:
    """Determine how long until next week's game night.

    Returns:
        int: Seconds to wait
    """
    now = dt.datetime.now()
    end = (now + dt.timedelta(days=7)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return (end - now).total_seconds()


def get_user(guild: Optional[discord.Guild], user: int) -> str:
    """Find the user in the guild

    Args:
        guild (Optional[discord.Guild]): Guild of the bot
        user (int): user id

    Returns:
        str: mentionable string or plain string
    """
    if not guild:
        return "User not found"
    return member.mention if (member := guild.get_member(user)) else "User not found"


async def update_mistborn_leaderboard(member: discord.User | discord.Member) -> int:
    """Update the mistborn leaderboard

    Args:
        member (discord.Member): User who made the mention.

    Returns:
        int: Number of mentions
    """
    with MIST.open() as fs:
        data: dict[str, list[int]] = json.load(fs)
    last_count, user_id = data.setdefault(member.name, [0, member.id])
    data[member.name] = [last_count + 1, user_id]
    with MIST.open("w") as fs:
        json.dump(data, fs, indent=2)
    return last_count + 1


@dataclass(slots=True)
class GameNight:
    announcer: Optional[discord.User]
    last_game_night_announced: Optional[dt.date] = None


def main() -> None:
    """
    The main bot. Has commands for team, teams, and chaos.
    """
    config = configparser.ConfigParser()
    config.read(INI)
    bot_token = config["DISCORD"]["BOT_TOKEN"]
    # announcements_channel_id = int(config["DISCORD"]["ANNOUNCEMENTS_CHANNEL_ID"])
    # game_night_channel_id = int(config["DISCORD"]["GAME_NIGHT_CHANNEL_ID"])
    # game_night_host_id = int(config["DISCORD"]["GAME_NIGHT_USER"])

    champs, champ_positions = get_champs()

    intents = discord.Intents(
        messages=True,
        members=True,
        message_content=True,
        guilds=True,
    )
    bot = commands.Bot(command_prefix="!", intents=intents)

    # announcements_channel = bot.get_channel(announcements_channel_id)
    # game_night_channel = bot.get_channel(game_night_channel_id)
    # game_night = GameNight(bot.get_user(game_night_host_id))

    @bot.command(name="team", help="Responds with a random team")
    async def on_message(ctx: commands.Context[Any]) -> None:  # type: ignore
        """
        (1) 5 champ team with roles based on where they normally play
        """
        await ctx.send("\n".join(make_team(champ_positions)))

    @bot.command(name="teams", help="Responds with two random teams")
    async def on_message(ctx: commands.Context[Any]) -> None:  # type: ignore
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
    async def on_message(ctx: commands.Context[Any]) -> None:  # type: ignore
        """
        (2) 5 champ teams with roles and builds fully random
        """
        response = ""
        for side in "AB":
            squad = "\n> ".join(make_chaos(champs))
            response += f"Side {side}\n> {squad}\n"

        await ctx.send(response.strip())  # Remove tailing '\n'

    @bot.command(
        name="jailtime",
        help="Get the total amount of time the user has spent in timeout.",
    )
    async def on_message(  # type: ignore
        ctx: commands.Context[Any], *args: discord.Member
    ) -> None:
        """
        How long the supplied users have been in jail.
        """
        now = dt.datetime.utcnow()
        guild = ctx.guild
        with TIMEOUTS.open() as fs:
            data: TIMEOUT = json.load(fs)
        if args:
            # Show a user or multiple users
            response: list[str] = []
            for user in args:
                found = data.get(user.name, (0, 0, False, user.id))
                timeouts, total_time = get_user_timeout_data(now, found)
                response.append(
                    f"{user.mention} has been in timeout {timeouts} times for {seconds_to_hms(total_time)}."
                )
        elif data is not None:
            # Show the leaderboard
            leaderboard = get_timeout_leaderboard(now, data)
            padding = 20
            response = [
                "Most timed out:",
                "-" * padding,
                "\n".join(
                    f"{idx}: {user[0]} | {get_user(guild, user[1])}"
                    for idx, user in enumerate(leaderboard[0])
                ),
                "-" * padding,
                "Longest timed out:",
                "-" * padding,
                "\n".join(
                    f"{idx}: {user[0]} | {get_user(guild, user[1])}"
                    for idx, user in enumerate(leaderboard[1])
                ),
            ]
        else:
            response = ["No timeouts yet."]
        await ctx.send("\n".join(response))

    @bot.command(
        name="mistborn",
        help="Show the Mistborn/Sanderson leaderboard",
    )
    async def on_message(ctx: commands.Context[Any]) -> None:  # type: ignore
        """
        Show the leaderboard of Mistborn / Sanderson mentions
        """
        with MIST.open() as fs:
            data: dict[str, list[int]] = json.load(fs)
        leaderboard = sorted(
            [v for v in data.values()], key=lambda x: x[0], reverse=True
        )
        guild = ctx.guild

        res = ["Mistbon / Sanderson leaderboard"]
        for idx, (mentions, user_id) in enumerate(leaderboard):
            res.append(f"{idx}: {mentions} | {get_user(guild, user_id)}")
        await ctx.send("\n".join(res))

    @bot.event
    async def on_member_update(before: discord.Member, after: discord.Member) -> None:  # type: ignore
        """
        Update the stored dictionary of user timeouts.
        """

        def check_for_timeout(roles: list[discord.Role]) -> bool:
            for role in roles:
                if role.id == 937779479676338196:
                    return True
            return False

        now = dt.datetime.utcnow()
        before_timeout = check_for_timeout(before.roles)
        after_timeout = check_for_timeout(after.roles)
        if before_timeout == after_timeout:
            # No change, do nothing.
            return
        if before_timeout:
            await entered_timeout(before, now)
        else:
            await left_timeout(before, now)

    @bot.listen("on_message")
    async def someone_mentioned_mistborn(msg: discord.Message) -> None:  # type: ignore
        """
        Update the mistborn leaderboard when someone mentions Mistborn or Sanderson.

        Args:
            msg (discord.Message): Message sent
        """
        if (message := msg.content.lower()) == "!mistborn":
            # Don't count when the command is called.
            return
        if "sanderson" in message or "mistborn" in message:
            mentions = await update_mistborn_leaderboard(msg.author)
            await msg.channel.send(f"{msg.author.mention} has mentioned Mistborn or Sanderson {mentions} time(s).")

    # @bot.listen("on_message")
    # async def game_night_announcement(message: discord.Message) -> None:
    #     """Check if the game night announcement happened."""
    #     if (
    #         message.channel == announcements_channel
    #         and "game night" in message.content.lower()
    #     ):
    #         game_night.last_game_night_announced = message.created_at.date()
    #     await bot.process_commands(message)

    # @tasks.loop(hours=1)
    # async def did_pyn_accounce_gamenight() -> None:
    #     """Ping PYN until he announces gamenight."""
    #     if not isinstance(announcements_channel, discord.TextChannel) or not isinstance(
    #         game_night_channel, discord.TextChannel
    #     ):
    #         return
    #     if (today := dt.datetime.now()).weekday() == 3 and 7 <= today.hour <= 20:
    #         # is it Thursday at 7:00 am?
    #         message = message_pyn()
    #         while game_night.last_game_night_announced != today.date():
    #             await game_night_channel.send(
    #                 f"{game_night.announcer.mention} {next(message)}"
    #                 if game_night.announcer
    #                 else next(message)
    #             )

    bot.run(bot_token, log_handler=handler)


def file_initialize(file: Path) -> None:
    """Initialize the empty file if it does not exist

    Args:
        file (Path): File needed.
    """
    if file.exists():
        return
    with file.open("w") as fs:
        json.dump({}, fs, indent=2)


if __name__ == "__main__":
    for file in (MIST, TIMEOUTS):
        file_initialize(file)
    main()
