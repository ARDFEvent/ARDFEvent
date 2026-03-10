import sys
from pathlib import Path

from dateutil.parser import parser
from sqlalchemy import Engine

import api


def get_templates_path():
    return ((Path(__file__).parent / "templates").absolute()) if not getattr(sys, "frozen", False) else str(
        Path(sys._MEIPASS) / "exports" / "templates")


def get_event(db: Engine):
    basic_info = api.get_basic_info(db)
    race_time = parser().parse(basic_info["date_tzero"])

    return {
        "name": basic_info["name"],
        "date": race_time.strftime("%d. %m. %Y"),
        "first_start": race_time.strftime("%H:%M"),
        "organizer": basic_info["organizer"],
        "limit": basic_info["limit"],
        "band": basic_info["band"],
    }
