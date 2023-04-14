"""
Functions for dealing with users.
"""

import datetime as dt
import json
import logging
from typing import Iterator, Optional

import discord

from paths import MIST, PROJ_PATH, TIMEOUTS

LOGGER = logging.getLogger("debug")
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(
    logging.FileHandler(filename=PROJ_PATH / "debug.log", encoding="utf-8", mode="w")
)

TIMEOUT = dict[str, tuple[int, int, str | bool, int]]


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
        LOGGER.error("%s left timeout when not in it.", user.display_name)
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
