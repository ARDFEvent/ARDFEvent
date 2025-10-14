from datetime import timedelta, datetime, timezone

from sqlalchemy import Engine

MODE = "rust"


def format_delta(td: timedelta):
    mins = td.seconds // 60
    secs = td.seconds - mins * 60
    return f"{mins:02}:{secs:02}"


def calculate_category_rust(db: Engine, name: str, include_unknown: bool = False):
    return calculate_category_raw(db.url.database, name, include_unknown)


if MODE == "py":
    # noinspection PyUnresolvedReferences
    from py_results import calculate_category, Result
elif MODE == "rust":
    # noinspection PyUnresolvedReferences
    from rust_results import calculate_category as calculate_category_raw
    # noinspection PyUnresolvedReferences
    from rust_results import OResult as Result


    def calculate_category(db: Engine, name: str, include_unknown: bool = False):
        return calculate_category_raw(db.url.database, name, include_unknown,
                                      datetime.now().replace(tzinfo=timezone.utc))
