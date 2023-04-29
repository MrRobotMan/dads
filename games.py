"""
Gather information on other games.
"""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime
from typing import Any, Iterable

from attr import dataclass

PROMO = dict[str, list[dict[str, list[dict[str, str]]]]]
PRICE = dict[str, dict[str, int]]
GAME = dict[str, str | PROMO | PRICE]


@dataclass(slots=True)
class EpicGame:
    title: str
    url: str
    price: int
    promo: tuple[str, str] | None

    @classmethod
    def from_json(cls, json_data: dict[str, Any]) -> EpicGame:
        """Build a game from the json data"""
        url = json_data["catalogNs"]["mappings"][0]["pageSlug"]
        return cls(
            title=json_data["title"],
            url=f"https://launcher.store.epicgames.com/en-US/p/{url}",
            price=json_data["price"]["totalPrice"]["discountPrice"],
            promo=get_promo_dates(json_data),
        )

    def valid(self) -> bool:
        """Check that a game is valid"""
        if self.promo is None:
            return False
        today = datetime.now()
        start = datetime.strptime(self.promo[0].split("T")[0], "%Y-%m-%d")
        end = datetime.strptime(self.promo[1].split("T")[0], "%Y-%m-%d")
        return start.date() <= today.date() <= end.date()


def get_promo_dates(data: dict[str, Any]) -> tuple[str, str] | None:
    """Parse the promos dict for current dates"""
    promo = data.get("promotions")
    if promo is None:
        return None
    offers = promo["promotionalOffers"]
    if len(offers) == 0:
        return None
    dates = offers[0]["promotionalOffers"][0]
    return (dates["startDate"], dates["endDate"])


def epic_free_games(show_all_data: bool = False) -> Iterable[str]:
    """Get the free games of the week from epic."""
    site = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
    response = urllib.request.urlopen(site)
    if response.code != 200:
        return ["No Games Found"]
    data = json.loads(response.read())
    raw_games: list[GAME] = data["data"]["Catalog"]["searchStore"]["elements"]
    games = [EpicGame.from_json(game) for game in raw_games]
    if show_all_data:
        print(*[game for game in games if game.valid() and game.price == 0], sep="\n")
    return (game.url for game in games if game.valid() and game.price == 0)


if __name__ == "__main__":
    with open("games.json", "w", encoding="utf8") as fp:
        json.dump(list(epic_free_games(True)), fp)
