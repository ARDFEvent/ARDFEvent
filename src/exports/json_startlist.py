import json
from datetime import datetime

from sqlalchemy import Engine, Select
from sqlalchemy.orm import Session

import api
from models import Category, Runner
from results import format_delta


def export(db: Engine) -> str:
    sess = Session(db)
    date_tzero = datetime.fromisoformat(api.get_basic_info(db)["date_tzero"])
    categories_db = sess.scalars(Select(Category).order_by(Category.name.asc())).all()

    runners = []
    for category in categories_db:
        for person in sess.scalars(
                Select(Runner)
                        .where(Runner.category == category)
                        .order_by(Runner.startlist_time.asc())
        ).all():
            starttime = person.startlist_time
            if not starttime:
                starttime_txt = None
            else:
                starttime_txt = starttime.strftime("%H:%M:%S")
            runners.append(
                {
                    "start_number": person.startno,
                    "first_name": person.name.split(", ")[1],
                    "last_name": person.name.split(", ")[0],
                    "competitor_index": person.reg,
                    "si_number": person.si,
                    "start_time_real": starttime_txt,
                    "start_time_relative": (
                        format_delta(
                            starttime.replace(tzinfo=None)
                            - date_tzero.replace(tzinfo=None)
                        )
                        if starttime
                        else ""
                    ),
                    "country": "CZE",
                }
            )

    sess.close()

    return json.dumps(runners, indent=4, default=str)
