import json
from pathlib import Path

import requests


def map_runner(orig: dict):
    return {
        "name": f"{orig["last_name"]}, {orig["first_name"]}",
        "reg": orig["index"],
        "si": 0,
        "byear": orig["birth_year"],
        "country": orig["country"],
    }


def download():
    clubs_raw = requests.get("https://rob-is.cz/api/club/").json()

    runners_raw = requests.get("https://rob-is.cz/api/members_all/").json()[
        "all_members"
    ]
    with open(Path.home() / ".ardfevent/clubs.json", "w+") as cf, open(
        Path.home() / ".ardfevent/runners.json", "w+"
    ) as rf:
        clubs = {}

        for club in clubs_raw:
            if club["club_shortcut"] not in clubs:
                clubs[club["club_shortcut"]] = club["club_name"]

        json.dump(clubs, cf)

        json.dump(list(map(map_runner, runners_raw)), rf)
