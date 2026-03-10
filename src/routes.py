from sqlalchemy import Engine, Select
from sqlalchemy.orm import Session

import api
from ardfevent_rust.routes import Point, optimal_route, point_dist
from models import Category, Runner, Punch, Control


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
            used_control = sess.scalars(
                Select(Control).where(Control.code == control.code).where(Control.lat != None).where(
                    Control.lon != None)).one_or_none()
            if used_control:
                pnt = Point(id=control.id, lat=used_control.lat, lon=used_control.lon)
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


def calculate_runner_route(db: Engine, runner_id: int) -> int:
    with Session(db) as sess:
        runner = sess.scalars(Select(Runner).where(Runner.id == runner_id)).one_or_none()
        if not runner:
            return 0

        punches = sess.scalars(Select(Punch).where(Punch.si == runner.si)).all()
        if not punches:
            return 0

        sf = api.get_starts_finishes(db)
        if not runner.category.name in sf["categories"]:
            return 0
        if not (start := sf["starts"][sf["categories"][runner.category.name]["start"]]) or not (
                finish := sf["finishes"][sf["categories"][runner.category.name]["finish"]]):
            return 0
        dist = 0
        last_point = Point(id=0, lat=start["lat"], lon=start["lon"])
        for punch in punches:
            control = sess.scalars(Select(Control).where(Control.code == punch.code)).first()
            if control and control.lat is not None and control.lon is not None:
                p = Point(id=0, lat=control.lat, lon=control.lon)
                if last_point:
                    dist += point_dist(last_point, p)
                last_point = p
        dist += point_dist(last_point, Point(id=0, lat=finish["lat"], lon=finish["lon"]))
        return dist


def get_cat_lenght_str(db: Engine, category_name: str) -> str:
    return f"{int(round(calculate_category_route(db, category_name)[1], -1))} m"
