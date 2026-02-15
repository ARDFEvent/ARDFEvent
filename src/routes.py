from sqlalchemy import Engine, Select
from sqlalchemy.orm import Session

import api
from ardfevent_rust.routes import Point, optimal_route
from models import Category


def calculate_category_route(db: Engine, category_name: str) -> tuple[list[Point], int]:
    with Session(db) as sess:
        cat = sess.scalars(Select(Category).where(Category.name == category_name)).one_or_none()
        if not cat:
            return [], 0
        starts_finishes = api.get_starts_finishes(db)
        points = []
        points_dict = {}
        if category_name not in starts_finishes["categories"]:
            return [], 0
        else:
            try:
                start = starts_finishes["starts"][starts_finishes["categories"][category_name]["start"]]
                finish = starts_finishes["finishes"][starts_finishes["categories"][category_name]["finish"]]
            except IndexError:
                return [], 0
            spoint = Point(id=9998, lat=start["lat"], lon=start["lon"])
            points.append(spoint)
            finish_point = Point(id=9999, lat=finish["lat"], lon=finish["lon"])

            points_dict[9998] = spoint
            points_dict[9999] = finish_point

        for control in cat.controls:
            if control.lat is not None and control.lon is not None:
                pnt = Point(id=control.id, lat=control.lat, lon=control.lon)
                points.append(pnt)
                points_dict[control.id] = pnt
            else:
                return [], 0

        points.append(finish_point)

        rust_points, length = optimal_route(points)
        result = []

        for point in rust_points:
            result.append(points_dict[point])

        return result, length * 1000


def get_lenght_str(db: Engine, category_name: str) -> str:
    return f"{int(round(calculate_category_route(db, category_name)[1] / 1000, 2) * 1000)} m"
