import json
from datetime import timedelta

from sqlalchemy import Engine, Select
from sqlalchemy.orm import Session

import api
import results
from models import Category, Control


def export(db: Engine) -> str:
    sess = Session(db)

    scal_controls = sess.scalars(Select(Control)).all()
    controls_list = {}
    for control in scal_controls:
        controls_list[control.name] = control.code

    categories = sess.scalars(Select(Category).order_by(Category.name.asc())).all()

    cat_props = []
    res_arr = []

    for category in categories:
        name = category.name
        controls = list(
            map(lambda x: {"si_code": x.code, "control_type": "BEACON" if x.name in ["M", "S"] else "CONTROL"},
                category.controls))
        band = ["M2", "M80", "COMBINED"][
            api.BANDS.index(api.get_basic_info(db)["band"])
        ]

        cat_props.append(
            {
                "category_name": name,
                "category_race_band": band,
                "category_time_limit": int(api.get_basic_info(db)["limit"]),
                "category_control_points": controls,
            }
        )

        results_cat = results.calculate_category(db, name)
        for person in results_cat:
            if person.status == "DNS":
                continue
            order = []
            last = person.start
            for punch in person.order:
                order.append(
                    {
                        "code": controls_list[punch[0].strip("+")],
                        "control_type": "CONTROL" if punch[0] != "M" else "BEACON",
                        "punch_status": punch[2],
                        "split_time": results.format_delta(punch[1] - last),
                    }
                )
                last = punch[1]
            if person.finish:
                order.append(
                    {
                        "code": 0,
                        "control_type": "FINISH",
                        "split_time": results.format_delta(person.finish - last),
                        "punch_status": "OK",
                    }
                )
            res_arr.append(
                {
                    "competitor_category": category.name,
                    "competitor_club": person.club,
                    "place": person.place if person.place != 0 else person.status,
                    "start_number": None,
                    "last_name": person.name.split(", ")[0],
                    "first_name": person.name.split(", ")[1],
                    "si_number": person.si,
                    "competitor_index": person.reg,
                    "competitor_gender": False,
                    "country": "CZE",
                    "result": {
                        "place": person.place,
                        "punch_count": person.tx,
                        "run_time": results.format_delta(timedelta(seconds=person.time)),
                        "result_status": person.status,
                        "punches": order,
                    },
                }
            )

    aliases = [{"alias_si_code": 0, "alias_name": "F"}]

    for cont in sess.scalars(Select(Control)).all():
        for alias in aliases:
            if alias["alias_si_code"] == cont.code:
                alias["alias_name"] += f"/{cont.name}"
                break
        else:
            aliases.append({"alias_si_code": cont.code, "alias_name": cont.name})

    sess.close()

    return json.dumps(
        {"categories": cat_props, "aliases": aliases, "competitors": res_arr}, default=str
    )
