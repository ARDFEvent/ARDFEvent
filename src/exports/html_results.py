from datetime import timedelta

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import Select
from sqlalchemy.orm import Session

import results
import routes
from exports import html_common
from models import Category


def export(filename, db, splits=False):
    if not filename.endswith(".html"):
        filename += ".html"

    with open(filename, "w+") as f:
        f.write(generate(db, splits=splits))


def generate(db, splits=False):
    sess = Session(db)
    categories = []
    categories_db = sess.scalars(Select(Category).order_by(Category.name.asc())).all()

    for category in categories_db:
        runners = []
        results_cat = list(
            filter(
                lambda x: x.status != "DNS",
                results.calculate_category(db, category.name),
            )
        )

        if not len(results_cat):
            continue

        for person in results_cat:
            if person.place == 0:
                place = person.status
            else:
                place = f"{person.place}."

            runner_splits = []

            if person.start:
                last = person.start

                for control in person.order:
                    runner_splits.append(
                        {
                            "control": control[0],
                            "time": results.format_delta(control[1] - person.start),
                            "split": results.format_delta(control[1] - last),
                        }
                    )
                    last = control[1]

            runners.append(
                {
                    "place": place,
                    "name": person.name,
                    "reg": person.reg,
                    "time": results.format_delta(timedelta(seconds=person.time)),
                    "tx": person.tx,
                    "order": " - ".join(
                        map(
                            lambda x: (
                                f'<span style="color: orange;">{x[0]}</span>'
                                if x[2] == "AP"
                                else x[0]
                            ),
                            person.order,
                        ),
                    ),
                    "splits": runner_splits,
                    "ok": person.status == "OK",
                }
            )
        categories.append(
            {
                "name": category.name,
                "length": routes.get_cat_lenght_str(category.name),
                "controls": ", ".join(map(lambda x: x.name, category.controls)),
                "runners": runners,
            }
        )

    sess.close()

    env = Environment(
        loader=FileSystemLoader(html_common.get_templates_path()), autoescape=select_autoescape()
    )
    return env.get_template("results.html").render(
        event=html_common.get_event(db), categories=categories, splits=splits
    )
