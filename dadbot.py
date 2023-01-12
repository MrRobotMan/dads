"""
Bot for DADS discord server.
Name: dadbot
Purpose: Have fun and troll folks.
Tasks so far:
    Create random teams
    Track when people are in timeout
    Track mentions of Sanderson / Mistborn
    Gently remind PYN to announce gamenight
"""

import configparser
import datetime as dt
import json
import logging
import random
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import DefaultDict, Iterator, Optional

import discord
from discord.ext import commands, tasks

PROJ_PATH = Path(__file__).parent
TIMEOUTS = PROJ_PATH / "timeouts.json"
MIST = PROJ_PATH / "mistborn.json"
CHAMPS = PROJ_PATH / "champs.json"
INI = PROJ_PATH / "env.ini"
TIMEOUT = dict[str, tuple[int, int, str | bool, int]]
MISTBORN = dt.timedelta(minutes=10)

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
    with CHAMPS.open() as json_file:
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
        tuple[Iterator[tuple[int, int]], ...]]: users and timeouts count / total time.
    """
    logger.debug(data)
    compiled = {
        (*get_user_timeout_data(time, v), idx): v[3]
        for idx, v in enumerate(data.values())
    }
    most_timed_out = sorted(list(compiled.items()), key=lambda x: x[0][0], reverse=True)
    long_timed_out = sorted(list(compiled.items()), key=lambda x: x[0][1], reverse=True)
    return (
        ((user[0][0], user[1]) for user in most_timed_out[:5]),
        ((user[0][1], user[1]) for user in long_timed_out[:5]),
    )


async def entered_timeout(user: discord.Member, time: dt.datetime) -> None:
    """Record the timeout into the log.

    Args:
        user (discord.Member): User in timeout
        time (dt.datetime): Time of timeout
    """
    with TIMEOUTS.open() as json_file:
        data: TIMEOUT = json.load(json_file)
    existing = data.setdefault(user.name, (0, 0, True, user.id))
    number_of_timeouts = existing[0] + 1
    data[user.name] = (
        number_of_timeouts,
        existing[1],
        time.strftime("%Y-%m-%d, %H:%M:%S"),
        user.id,
    )
    with TIMEOUTS.open("w+") as json_file:
        json.dump(data, json_file, indent=2)


async def left_timeout(user: discord.Member, time: dt.datetime) -> None:
    """Record the timeout into the log.

    Args:
        user (discord.Member): User no longer in timeout
        time (dt.datetime): Time of timeout ending
    """
    with TIMEOUTS.open() as json_file:
        data: TIMEOUT = json.load(json_file)
    existing = data.setdefault(user.name, (0, 0, False, user.id))
    duration = existing[1]
    if isinstance(existing[2], bool):
        logger.error("%s left timeout when not in it.", user.display_name)
    else:
        last_put_in_timeout = dt.datetime.strptime(existing[2], "%Y-%m-%d, %H:%M:%S")
        duration += (time - last_put_in_timeout).total_seconds()
    data[user.name] = (
        existing[0],
        int(duration),
        False,
        user.id,
    )
    with TIMEOUTS.open("w+") as json_file:
        json.dump(data, json_file, indent=2)


def get_user(guild: Optional[discord.Guild], user: int | str) -> str:
    """Find the user in the guild

    Args:
        guild (Optional[discord.Guild]): Guild of the bot
        user (int): user id

    Returns:
        str: User's display name or "user not found"
    """
    if not guild:
        return "User not found"
    return (
        member.display_name
        if (member := guild.get_member(int(user)))
        else "User not found"
    )


async def update_mistborn_leaderboard(
    member: discord.User | discord.Member, mentions: int
) -> int:
    """Update the mistborn leaderboard

    Args:
        member (discord.Member): User who made the mention.
        mentions (int): Number of mentions in the message.
    Returns:
        int: Number of mentions
    """
    with MIST.open() as json_file:
        data: dict[str, int] = json.load(json_file)
    last_count = data.setdefault(str(member.id), 0)
    data[str(member.id)] = last_count + mentions
    with MIST.open("w") as json_file:
        json.dump(data, json_file, indent=2)
    return last_count + 1


@dataclass(slots=True)
class GameNight:
    """Object to track the game night announcements."""

    announcer: Optional[discord.User] = None
    announcements_channel: Optional[discord.TextChannel] = None
    game_night_channel: Optional[discord.TextChannel] = None
    last_game_night_announced: Optional[dt.date] = None
    message_index: int = field(init=False, default=0)
    messages = (
        "Did you know it's Thursday{}?",
        "Still no Thursday announcement{}...",
        "Hello{}? Thursday",
        "What's the polite *Canadian *way to say this..Have you noticed the time{}?",
        "Have you no shame{}? We expect jr officers to post on time!",
        "Is it just me, or is{} *late*?",
        (
            "Sometimes I think our jr officer wants to remain a jr officer forever. "
            "Do you want to be promoted{}?"
        ),
        (
            "Time's tickin'{} and if you dont post it soon, it'll be "
            "[Friday](https://www.youtube.com/watch?v=iCFOcqsnc9Y)"
        ),
        (
            "Some people must think we tolerate late game night announcements "
            "around here{}. We dont."
        ),
    )

    @property
    def message(self) -> str:
        """Message the gamenight host with the next message."""
        message = self.messages[self.message_index]
        self.message_index = (self.message_index + 1) % len(self.messages)
        if self.announcer is not None:
            mention = f" {self.announcer.mention}"
        else:
            mention = ""
        return message.format(mention)

    def mission_accomplished(self) -> None:
        """Reset the message index"""
        self.message_index = 0


def main() -> None:
    """
    The main bot. Has commands for team, teams, and chaos.
    """
    config = configparser.ConfigParser()
    config.read(INI)
    bot_token = config["DISCORD"]["BOT_TOKEN"]
    announcements_channel_id = int(config["DISCORD"]["ANNOUNCEMENTS_CHANNEL_ID"])
    game_night_channel_id = int(config["DISCORD"]["GAME_NIGHT_CHANNEL_ID"])
    game_night_host_id = int(config["DISCORD"]["GAME_NIGHT_USER"])
    barnmol = config["DISCORD"]["MISTBORN_BEST_USER"]
    administrator = int(config["DISCORD"]["ADMIN"])

    champs, champ_positions = get_champs()
    sanderson_messages: dict[int, dt.datetime] = {}  # int is channel id

    intents = discord.Intents(
        messages=True,
        members=True,
        message_content=True,
        guilds=True,
    )
    bot = commands.Bot(command_prefix="!", intents=intents)
    game_night = GameNight()

    @bot.event
    async def on_ready() -> None:
        announcements_channel = bot.get_channel(announcements_channel_id)
        game_night_channel = bot.get_channel(game_night_channel_id)
        if not isinstance(announcements_channel, discord.TextChannel) or not isinstance(
            game_night_channel, discord.TextChannel
        ):
            return
        game_night.announcements_channel = announcements_channel
        game_night.game_night_channel = game_night_channel
        game_night.announcer = bot.get_user(game_night_host_id)
        did_pyn_announce_gamenight.start()

    @bot.command(name="team", help="Responds with a random team")
    async def on_message(ctx: commands.Context[commands.Bot]) -> None:
        """
        (1) 5 champ team with roles based on where they normally play
        """
        await ctx.send("\n".join(make_team(champ_positions)))

    @bot.command(name="teams", help="Responds with two random teams")
    async def on_message(ctx: commands.Context[commands.Bot]) -> None:
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
    async def on_message(ctx: commands.Context[commands.Bot]) -> None:
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
    async def on_message(
        ctx: commands.Context[commands.Bot], *args: discord.Member
    ) -> None:
        """
        How long the supplied users have been in jail.
        """
        now = dt.datetime.utcnow()
        guild = ctx.guild
        with TIMEOUTS.open() as json_file:
            data: TIMEOUT = json.load(json_file)
        if args:
            # Show a user or multiple users
            response: list[str] = []
            for user in args:
                found = data.get(user.name, (0, 0, False, user.id))
                timeouts, total_time = get_user_timeout_data(now, found)
                response.append(
                    (
                        f"{user.mention} has been in timeout {timeouts} times "
                        f"for {seconds_to_hms(total_time)}."
                    )
                )
        elif data is not None:
            # Show the leaderboard
            leaderboard = get_timeout_leaderboard(now, data)
            padding = 30
            response = [
                "```Most timed out:",
                "-" * padding,
                "\n".join(
                    f"{idx:2}: {user[0]:<4} | {get_user(guild, user[1])}"
                    for idx, user in enumerate(leaderboard[0], start=1)
                ),
                "-" * padding,
                "Longest timed out:",
                "-" * padding,
                "\n".join(
                    f"{idx:2}: {seconds_to_hms(user[0])} | {get_user(guild, user[1])}"
                    for idx, user in enumerate(leaderboard[1], start=1)
                ),
                "```",
            ]
        else:
            response = ["No timeouts yet."]
        await ctx.send("\n".join(response))

    @bot.command(
        name="mistborn",
        help="Show the Mistborn/Sanderson leaderboard",
    )
    async def on_message(ctx: commands.Context[commands.Bot]) -> None:
        """
        Show the leaderboard of Mistborn / Sanderson mentions
        """

        with MIST.open() as json_file:
            data: dict[str, int] = json.load(json_file)
        leaderboard = sorted(data.items(), key=lambda x: x[1], reverse=True)
        guild = ctx.guild

        res = ["```Mistborn / Sanderson Top 10 Leaderboard"]
        for idx, (user_id, mentions) in enumerate(leaderboard[:10], start=1):
            res.append(f"{idx:2}: {mentions:<4} | {get_user(guild, user_id)}")
        if barnmol not in (leader[0] for leader in leaderboard[:10]):
            res.append(
                f"\nHonorary Mention: {get_user(guild, barnmol)} with {data[barnmol]}"
            )
        res.append("```")
        await ctx.send("\n".join(res))

    @bot.event
    async def on_member_update(before: discord.Member, after: discord.Member) -> None:
        """
        Update the stored dictionary of user timeouts.
        """

        def check_for_timeout(roles: list[discord.Role]) -> bool:
            for role in roles:
                # Timeout role
                if role.id == 937779479676338196:
                    return True
            return False

        now = dt.datetime.utcnow()
        before_timeout = check_for_timeout(before.roles)
        after_timeout = check_for_timeout(after.roles)
        if before_timeout == after_timeout:
            # No change, do nothing.
            return
        if after_timeout:
            await entered_timeout(before, now)
        else:
            await left_timeout(before, now)

    @bot.listen("on_message")
    async def someone_mentioned_mistborn(msg: discord.Message) -> None:
        """
        Update the mistborn leaderboard when someone mentions Mistborn or Sanderson.

        Args:
            msg (discord.Message): Message sent
        """
        if (message := msg.content.lower()) == "!mistborn" or msg.author == bot.user:
            # Don't count when the command is called or if the dadbot does it.
            return
        if cnt := message.count("sanderson") + message.count("mistborn"):
            mentions = await update_mistborn_leaderboard(msg.author, cnt)
            last_response = sanderson_messages.get(msg.channel.id)
            if (
                last_response := sanderson_messages.get(msg.channel.id)
            ) and dt.datetime.now(tz=dt.timezone.utc) - last_response < MISTBORN:
                return
            response = await msg.channel.send(
                f"{msg.author.display_name} has mentioned Mistborn or Sanderson {mentions} time(s)."
            )
            sanderson_messages[msg.channel.id] = response.created_at

    @bot.listen("on_message")
    async def game_night_announcement(message: discord.Message) -> None:
        """Check if the game night announcement happened."""
        if (
            message.channel == game_night.announcements_channel
            and game_night.announcer == message.author
            and message.embeds  # non-empty list if there's an embedded image.
        ):
            game_night.last_game_night_announced = message.created_at.date()

    @tasks.loop(minutes=43)
    async def did_pyn_announce_gamenight() -> None:
        """Ping PYN until he announces gamenight."""
        if (today := dt.datetime.now()).weekday() == 3 and 7 <= today.hour <= 20:
            # is it Thursday at 7:00 am?
            if (
                game_night.last_game_night_announced != today.date()
                and game_night.game_night_channel is not None
            ):
                await game_night.game_night_channel.send(game_night.message)
            else:
                game_night.mission_accomplished()

    @bot.command(name="badbot")
    async def kill_task(ctx: commands.Context[commands.Bot]) -> None:
        """Kill switch for the pyn announcement. Just in case."""
        did_pyn_announce_gamenight.stop()
        await ctx.message.channel.send("PYN task stopped.")

    @bot.command(name="goodbot")
    async def start_task(ctx: commands.Context[commands.Bot]) -> None:
        """Restart the pyn announcement."""
        if ctx.message.author.id != administrator:
            await ctx.message.channel.send(f"Nice try {ctx.message.author.mention}")
        else:
            try:
                did_pyn_announce_gamenight.start()
                await ctx.message.channel.send("PYN task started.")
            except RuntimeError:
                await ctx.message.channel.send("Task already running.")

    bot.run(bot_token, log_handler=handler)


def file_initialize(file: Path) -> None:
    """Initialize the empty file if it does not exist

    Args:
        file (Path): File needed.
    """
    if file.exists():
        return
    with file.open("w") as json_file:
        json.dump({}, json_file, indent=2)


if __name__ == "__main__":
    for lst in (MIST, TIMEOUTS):
        file_initialize(lst)
    main()
