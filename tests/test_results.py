from datetime import datetime, timezone

import pytest
import rust_results
from sqlalchemy import create_engine, Select
from sqlalchemy.orm import Session

import py_results
from migrations import migrate
from models import Category

TESTPATH = "/home/jacobcz/.ardfevent/test/testrace.sqlite"


def test_results():
    migrate(f"sqlite:///{TESTPATH}")
    eng = create_engine(f"sqlite:///{TESTPATH}")
    with Session(eng) as sess:
        for cat in sess.scalars(Select(Category)):
            now = int(datetime.now().replace(tzinfo=timezone.utc).timestamp())
            pyres = py_results.calculate_category(eng, cat.name, True, now)
            rustres = rust_results.calculate_category(TESTPATH, cat.name, True, now)
            assert len(pyres) == len(rustres)
            for p, r in zip(pyres, rustres):
                assert p.name == r.name
                assert p.reg == r.reg
                assert p.si == r.si
                assert p.tx == r.tx
                assert p.time == r.time
                assert p.status == r.status
                assert p.order == r.order
                assert p.club == r.club
                assert p.start == r.start
                assert p.finish == r.finish
                assert p.place == r.place
