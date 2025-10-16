import unittest
from datetime import datetime, timezone

import rust_results
from sqlalchemy import create_engine, Select
from sqlalchemy.orm import Session

import py_results
from models import Category

TESTPATH = "/home/jacobcz/.ardfevent/test/testrace.sqlite"


class TestResults(unittest.TestCase):
    def test_results(self):
        eng = create_engine(f"sqlite:///{TESTPATH}")
        with Session(eng) as sess:
            for cat in sess.scalars(Select(Category)):
                now = int(datetime.now().replace(tzinfo=timezone.utc).timestamp())
                pyres = py_results.calculate_category(eng, cat.name, True, now)
                rustres = rust_results.calculate_category(TESTPATH, cat.name, True, now)
                self.assertEqual(len(pyres), len(rustres))
                for p, r in zip(pyres, rustres):
                    self.assertEqual(p.name, r.name)
                    self.assertEqual(p.reg, r.reg)
                    self.assertEqual(p.si, r.si)
                    self.assertEqual(p.tx, r.tx)
                    self.assertEqual(p.time, r.time)
                    self.assertEqual(p.status, r.status)
                    self.assertEqual(p.order, r.order)
                    self.assertEqual(p.club, r.club)
                    self.assertEqual(p.start, r.start)
                    self.assertEqual(p.finish, r.finish)
                    self.assertEqual(p.place, r.place)


if __name__ == '__main__':
    unittest.main()
