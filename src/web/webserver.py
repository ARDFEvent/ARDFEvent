import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from wsgiref.simple_server import make_server

from pyramid.config import Configurator
from pyramid.httpexceptions import HTTPFound
from pyramid.request import Request
from pyramid.response import Response
from sqlalchemy import Select
from sqlalchemy.orm import Session

import api
import results
from models import Category


class ARDFEventServer:
    def __init__(self, db):
        self.db = db
        self.announcement = ""

    def results(self, request: Request):
        def res_to_resp(res: results.Result):
            def order_to_resp(order, start=None):
                resp = []
                if not start:
                    return []
                last = start

                for control in order:
                    resp.append(
                        [
                            control[0],
                            results.format_delta(control[1] - last),
                            control[2],
                        ]
                    )
                    last = control[1]

                return resp

            return {
                "name": res.name,
                "place": res.place,
                "club": res.club,
                "index": res.reg,
                "si": res.si,
                "time": (
                    results.format_delta(timedelta(seconds=res.time))
                    if res.time > 0
                    else "UNS"
                ),
                "tx": res.tx,
                "status": res.status,
                "start": (res.start or datetime.now()).strftime("%H:%M:%S"),
                "order": order_to_resp(res.order, res.start),
            }

        res = results.calculate_category(self.db, request.params["category"], True)
        resp = list(map(res_to_resp, res))

        return Response(
            json.dumps(resp), content_type="application/json", charset="UTF-8"
        )

    def categories(self, request: Request):
        sess = Session(self.db)

        result = {}
        cats = sess.scalars(Select(Category)).all()
        for cat in cats:
            result[cat.name] = ", ".join(map(lambda x: x.name, cat.controls))

        sess.close()

        return Response(
            json.dumps(result), content_type="application/json", charset="UTF-8"
        )

    def get_announcement(self, request: Request):
        return Response(
            json.dumps({"ann": self.announcement, "robis": bool(api.get_basic_info(self.db)["robis_api"])}),
            content_type="application/json",
            charset="UTF-8",
        )

    def run_server(self):
        with Configurator() as config:
            config.add_route("static", "/static")
            config.add_static_view(
                name="static",
                path=(
                    str((Path(__file__).parent / "static").absolute())
                    if not getattr(sys, "frozen", False)
                    else str(Path(sys._MEIPASS) / "web" / "static")
                ),
            )

            config.add_route("home", "/")
            config.add_view(lambda x, y: HTTPFound(location="/static/setup.html"), route_name="home")
            config.add_route("results", "/api/results")
            config.add_view(self.results, route_name="results")
            config.add_route("categories", "/api/categories")
            config.add_view(self.categories, route_name="categories")
            config.add_route("announcement", "/api/announcement")
            config.add_view(self.get_announcement, route_name="announcement")
            app = config.make_wsgi_app()
        server = make_server("127.0.0.1", 8080, app)
        server.serve_forever()
