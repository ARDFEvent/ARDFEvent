from datetime import datetime

from jinja2 import Environment, select_autoescape, FileSystemLoader
from sqlalchemy import Select
from sqlalchemy.orm import Session

import api
from exports import html_common
from models import Category, Runner
from results import format_delta


def export(filename, db):
    if not filename.endswith(".html"):
        filename += ".html"

    with open(filename, "w+") as f:
        f.write(generate(db))


def generate(db):
    sess = Session(db)
    date_tzero = datetime.fromisoformat(api.get_basic_info(db)["date_tzero"])
    categories = []
    categories_db = sess.scalars(Select(Category).order_by(Category.name.asc())).all()

    for category in categories_db:
        runners = []
        for person in sess.scalars(
                Select(Runner)
                        .where(Runner.category == category)
                        .order_by(Runner.startlist_time.asc())
        ).all():
            starttime = person.startlist_time
            if starttime is None:
                starttime_txt = "-"
            else:
                starttime_txt = starttime.strftime("%H:%M:%S")
            runners.append(
                {
                    "name": person.name,
                    "reg": person.reg,
                    "si": person.si,
                    "starttime_abs": starttime_txt,
                    "starttime_rel": (
                        format_delta(
                            starttime.replace(tzinfo=None)
                            - date_tzero.replace(tzinfo=None)
                        )
                        if starttime
                        else "-"
                    ),
                }
            )
        if len(runners):
            categories.append(
                {
                    "name": category.name,
                    "controls": category.display_controls,
                    "runners": runners,
                }
            )

    sess.close()

    env = Environment(loader=FileSystemLoader(html_common.get_templates_path()), autoescape=select_autoescape())
    return env.get_template("startlist.html").render(
        event=html_common.get_event(db), categories=categories
    )
