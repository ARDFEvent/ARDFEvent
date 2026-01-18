import json
from pathlib import Path

from sqlalchemy import Engine, Select
from sqlalchemy.orm import Session

from models import BasicInfo, Runner

BI_TEMPLATE = {
    "name": "NAME",
    "date_tzero": "DATE_TIME",
    "organizer": "ORG",
    "limit": "LIMIT",
    "band": "BAND",
    "robis_api": "ROBIS_API",
    "robis_id": "ROBIS_ID",
    "robis_etap": "ROBIS_ETAP",
}

BANDS = ["2m", "80m", "kombinované"]


def get_basic_info(database: Engine):
    sess = Session(database)
    result = {}

    for key in BI_TEMPLATE:
        val: BasicInfo | None = sess.scalars(
            Select(BasicInfo).where(BasicInfo.key == BI_TEMPLATE[key])
        ).one_or_none()
        if val:
            result[key] = val.value
        else:
            result[key] = None

    sess.close()

    return result


def set_basic_info(database: Engine, data: dict):
    sess = Session(database)

    for key in data:
        if not key in BI_TEMPLATE.keys():
            continue

        val: BasicInfo | None = sess.scalars(
            Select(BasicInfo).where(BasicInfo.key == BI_TEMPLATE[key])
        ).one_or_none()
        if val:
            val.value = data[key]
        else:
            sess.add(BasicInfo(key=BI_TEMPLATE[key], value=data[key]))

    sess.commit()
    sess.close()


def get_registered_runners():
    with open(Path.home() / ".ardfevent/runners.json", "r") as rf:
        return json.load(rf)


def get_registered_names():
    with open(Path.home() / ".ardfevent/runners.json", "r") as rf:
        return list(map(lambda x: x["name"], json.load(rf)))


def get_clubs():
    with open(Path.home() / ".ardfevent/clubs.json", "r") as cf:
        return json.load(cf)


def renumber_runners(database: Engine):
    sess = Session(database)

    runners = sess.scalars(Select(Runner)).all()
    runners_dict = {}

    for runner in runners:
        if runner.name in runners_dict:
            runners_dict[runner.name] += 1
            runner.name += f" ({runners_dict[runner.name]})"
        else:
            runners_dict[runner.name] = 0

    sess.commit()
    sess.close()
