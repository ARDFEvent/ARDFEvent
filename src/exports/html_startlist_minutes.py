from datetime import datetime

from jinja2 import Environment, select_autoescape, FileSystemLoader
from sqlalchemy import Select
from sqlalchemy.orm import Session

import api
from exports import html_common
from models import Runner
from results import format_delta


def export(filename, db):
    if not filename.endswith(".html"):
        filename += ".html"

    with open(filename, "w+") as f:
        f.write(generate(db))


def generate(db):
    sess = Session(db)
    date_tzero = datetime.fromisoformat(api.get_basic_info(db)["date_tzero"])
    minutes = []
    minutes_db = sess.scalars(
        Select(Runner.startlist_time).distinct().order_by(Runner.startlist_time.asc())
    ).all()

    for minute in minutes_db:
        if not minute:
            continue

        runners = []
        for person in sess.scalars(
                Select(Runner)
                        .where(Runner.startlist_time == minute)
                        .order_by(Runner.name.asc())
        ).all():
            runners.append(
                {
                    "name": person.name,
                    "reg": person.reg,
                    "si": person.si,
                    "category": person.category.name,
                }
            )
        minutes.append(
            {
                "abs": minute.strftime("%H:%M:%S"),
                "rel": format_delta(
                    (minute.replace(tzinfo=None) - date_tzero.replace(tzinfo=None))
                ),
                "runners": runners,
            }
        )

    sess.close()

    env = Environment(loader=FileSystemLoader(html_common.get_templates_path()), autoescape=select_autoescape())
    return env.get_template("startlist_minutes.html").render(
        event=html_common.get_event(db), minutes=minutes
    )
