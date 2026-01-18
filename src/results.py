from datetime import datetime, timedelta

from sqlalchemy import Engine, Select
from sqlalchemy.orm import Session

import api
from models import Category, Control, Punch


class Result:
    def __init__(
        self,
        name: str,
        reg: str,
        si: int,
        tx: int,
        time: int,
        status: str,
        order: list,
        club: str,
        start: datetime | None = None,
        finish: datetime | None = None,
    ):
        self.name = name
        self.reg = reg
        self.si = si
        self.tx = tx
        self.time = time
        self.status = status
        self.order = order
        self.place = 0
        self.club = club
        self.start = start
        self.finish = finish


def calculate_category(db: Engine, name: str, include_unknown: bool = False):
    limit = int(api.get_basic_info(db)["limit"])

    sess = Session(db)
    category = sess.scalars(Select(Category).where(Category.name == name)).first()

    results: list[Result] = []

    runners = category.runners
    controls = category.controls
    mandatory = list(map(lambda c: c.code, filter(lambda c: c.mandatory, controls)))
    cat_codes = list(map(lambda c: c.code, controls))

    for runner in runners:
        if runner.manual_dns:
            results.append(
                Result(
                    runner.name,
                    runner.reg,
                    runner.si,
                    0,
                    0,
                    "DNS",
                    [],
                    runner.club,
                    datetime.now(),
                )
            )
            continue
        elif runner.manual_disk:
            results.append(
                Result(
                    runner.name,
                    runner.reg,
                    runner.si,
                    0,
                    0,
                    "DSQ",
                    [],
                    runner.club,
                    datetime.fromtimestamp(0),
                )
            )
            continue

        loc_controls = cat_codes.copy()
        loc_mandatory = mandatory.copy()

        tx = 0
        mandatory_cnt = 0
        start = runner.startlist_time
        finish = None

        punches = sess.scalars(Select(Punch).where(Punch.si == runner.si)).all()
        order = []

        now = datetime.now()

        if len(punches) == 0:
            if include_unknown:
                results.append(
                    Result(
                        runner.name,
                        runner.reg,
                        runner.si,
                        0,
                        (
                            0
                            if not start
                            else (
                                now - start if now > start else -(start - now)
                            ).total_seconds()
                        ),
                        "?",
                        [],
                        runner.club,
                        start,
                    )
                )
            continue

        for punch in punches:
            if punch.code == 1000:
                start = punch.time
            elif punch.code == 1001:
                finish = punch.time
            elif punch.code in loc_controls:
                tx += 1
                control = list(filter(lambda c: c.code == punch.code, controls))
                order.append((control[0].name, punch.time, "OK"))
            else:
                control = sess.scalars(
                    Select(Control).where(Control.code == punch.code)
                ).one_or_none()
                if control:
                    order.append((f"{control.name}+", punch.time, "AP"))

            if punch.code in loc_mandatory:
                mandatory_cnt += 1
                try:
                    loc_mandatory.remove(punch.code)
                except:
                    ...

            try:
                loc_controls.remove(punch.code)
            except:
                ...

        status = "OK"

        if not start:
            start = api.get_basic_info(db)["date_tzero"]

        if not finish:
            status = "DNF"
            time = 0
        else:
            time = (finish - start).seconds

        if len(mandatory) > mandatory_cnt or tx - mandatory_cnt < 1 and status == "OK":
            status = "MP"
        elif time > limit * 60:
            status = "OVT"

        results.append(
            Result(
                runner.name,
                runner.reg,
                runner.si,
                tx,
                time,
                status,
                order,
                runner.club,
                start,
                finish,
            )
        )

    ok = list(filter(lambda x: x.status == "OK", results))
    running = list(filter(lambda x: x.status == "?", results))
    running.sort(key=lambda x: -x.time)
    nok = list(filter(lambda x: x.status not in ["OK", "?"], results))
    nok.sort(key=lambda x: (x.status, x.name))

    i = 0
    lastplace = 0

    ok.sort(key=lambda x: (-x.tx, x.time, x.name))

    lasttime = 0
    lasttx = 0
    for runner in ok:
        i += 1
        if runner.time == lasttime and runner.tx == lasttx:
            place = lastplace
        else:
            place = i
        runner.place = place
        lasttime = runner.time
        lasttx = runner.tx
        lastplace = place

    final_results = ok
    final_results += running
    final_results += nok

    sess.close()

    return final_results


def format_delta(td: timedelta):
    mins = td.seconds // 60
    secs = td.seconds - mins * 60
    return f"{mins:02}:{secs:02}"
