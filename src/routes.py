from sqlalchemy import Engine

from ardfevent_rust.routes import RouteEngine, Point

engine: RouteEngine | None = None


def init_engine(db: Engine):
    global engine
    engine = RouteEngine(db.url.database)


def invalidate_cache(category_name: str | None = None):
    if engine:
        engine.invalidate_cache(category_name)


def calculate_category_route(category_name: str) -> tuple[list[Point], float]:
    if not engine:
        return [], 0
    return engine.calculate_category_route(category_name)


def calculate_runner_route(runner_id: int) -> float:
    if not engine:
        return 0
    return engine.calculate_runner_route(runner_id)


def get_cat_lenght_str(category_name: str) -> str:
    return f"{int(round(calculate_category_route(category_name)[1], -1))} m"
