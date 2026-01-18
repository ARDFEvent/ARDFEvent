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

    i = 1

    for category in categories:
        name = category.name
        controls = ", ".join(map(lambda x: x.name, category.controls))
        band = ["M2", "M80", "COMBINED"][
            api.BANDS.index(api.get_basic_info(db)["band"])
        ]

        lim_int = int(api.get_basic_info(db)["limit"])
        lim_hrs = lim_int // 60
        lim_mins = lim_int % 60
        limit = f"{lim_hrs:02}:{lim_mins:02}"

        cat_props.append(
            {
                "category_name": name,
                "category_control_points": controls,
                "category_race_band": band,
                "category_time_limit": limit,
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
                        "alias": punch[0].strip("+"),
                        "control_type": "CONTROL" if punch[0] != "M" else "BEACON",
                        "punch_status": punch[2],
                        "split_time": results.format_delta(punch[1] - last),
                        "code": controls_list[punch[0].strip("+")],
                    }
                )
                last = punch[1]
            if person.finish:
                order.append(
                    {
                        "alias": "F",
                        "control_type": "FINISH",
                        "split_time": results.format_delta(person.finish - last),
                        "punch_status": "OK",
                        "code": 255,
                    }
                )
            res_arr.append(
                {
                    "competitor_category_name": category.name,
                    "place": person.place if person.place != 0 else person.status,
                    "start_number": i,
                    "last_name": person.name.split(", ")[0],
                    "first_name": person.name.split(", ")[1],
                    "si_number": person.si,
                    "punch_count": person.tx,
                    "run_time": results.format_delta(timedelta(seconds=person.time)),
                    "result_status": person.status,
                    "competitor_index": person.reg,
                    "country": "CZE",
                    "punches": order,
                }
            )
            i += 1

    sess.close()

    return json.dumps(
        {"category_properties": cat_props, "results": res_arr}, indent=4, default=str
    )
