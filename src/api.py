import json
from pathlib import Path

from sqlalchemy import Engine, Select, Update
from sqlalchemy.orm import Session

from models import BasicInfo, Runner, Control

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
CONFIG_PATH = Path.home() / ".ardfevent" / "config.json"


def migrate_basic_info(database: Engine):
    with Session(database) as sess:
        for new, old in BI_TEMPLATE.items():
            sess.execute(Update(BasicInfo).where(BasicInfo.key == old).values(key=new))

        sess.commit()


def get_basic_info(database: Engine):
    with Session(database) as sess:
        result = {}
        bi = sess.scalars(Select(BasicInfo)).all()
        for val in bi:
            result[val.key] = val.value

        return result


def set_basic_info(database: Engine, data: dict):
    with Session(database) as sess:
        for key in data:
            val: BasicInfo | None = sess.scalars(
                Select(BasicInfo).where(BasicInfo.key == key)
            ).one_or_none()
            if val:
                val.value = data[key]
            else:
                print("Added", key, data[key])
                sess.add(BasicInfo(key=key, value=data[key]))

        sess.commit()


def get_registered_runners():
    with open(Path.home() / ".ardfevent/runners.json", "r") as rf:
        return json.load(rf)


def get_registered_names():
    with open(Path.home() / ".ardfevent/runners.json", "r") as rf:
        return list(map(lambda x: x["name"], json.load(rf)))


def get_clubs():
    with open(Path.home() / ".ardfevent/clubs.json", "r") as cf:
        return json.load(cf)


def get_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def get_config_value(key, default=None):
    cfg = get_config()
    return cfg.get(key, default)


def set_config_value(key, value):
    cfg = get_config()
    cfg[key] = value
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)
    return cfg


def renumber_runners(database: Engine):
    with Session(database) as sess:
        runners = sess.scalars(Select(Runner)).all()
        runners_dict = {}

        for runner in runners:
            if runner.name in runners_dict:
                runners_dict[runner.name] += 1
                runner.name += f" ({runners_dict[runner.name]})"
            else:
                runners_dict[runner.name] = 0

        sess.commit()


def sort_controls(controls: list[Control]) -> list[Control]:
    def sort_key(control: Control) -> tuple[int, str]:
        if control.name in ["M", "B"]:
            return 99998, control.name
        if control.name in ["S", "D"]:
            return 99997, control.name
        if "R" in control.name or "F" in control.name:
            try:
                return int(control.name.strip("RF")), control.name
            except ValueError:
                ...
        try:
            return int(control.name), control.name
        except ValueError:
            return 99999, control.name

    return sorted(controls, key=sort_key)


def get_starts_finishes(db: Engine):
    return json.loads(get_basic_info(db).get("map_starts_finishes", '{"categories": {}, "starts": [], "finishes": []}'))
