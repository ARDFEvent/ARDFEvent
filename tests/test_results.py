import random
import time
from datetime import datetime, timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

import api
import results
from models import Punch
from py_results import calculate_category as py_calc_category


@pytest.fixture(scope="function")
def race_with_results(race_engine_file, faker):
    """
    Create a category, controls and many runners using fast bulk inserts instead of make_* helpers.
    This reduces fixture overhead significantly for large num_runners.
    """

    def _make(n=1000, fast=False):
        num_controls = random.randint(3, 6)
        num_runners = n

        with Session(race_engine_file, expire_on_commit=False) as session:
            total_controls = num_controls + random.randint(2, 4)
            base_code = 31
            control_codes = [base_code + i for i in range(total_controls)]

            base_control_id = faker.random_int(min=2000, max=300000)
            controls_data = []
            for i, code in enumerate(control_codes):
                controls_data.append({
                    "id": int(base_control_id + i),
                    "name": f"{i}",
                    "code": int(code),
                    "mandatory": False,
                    "spectator": False,
                    "lat": None,
                    "lon": None,
                })

            from models import Control, Category, Runner, control_associations

            session.execute(Control.__table__.insert(), controls_data)

            cat_name = f"M{faker.random_int(12, 80)}"
            category_id = int(faker.random_int(min=5000, max=400000))
            session.execute(Category.__table__.insert(),
                            [{"id": category_id, "name": cat_name, "display_controls": ""}])

            assoc_rows = [{"control_id": int(base_control_id + i), "category_id": int(category_id)} for i in
                          range(total_controls)]
            session.execute(control_associations.insert(), assoc_rows)

            session.execute(text("CREATE INDEX IF NOT EXISTS idx_punches_si_time ON punches(si, time);"))
            session.execute(text("CREATE INDEX IF NOT EXISTS idx_runners_category_id ON runners(category_id);"))

            start_si = 1000000
            runners_data = []
            sis = []
            for i in range(num_runners):
                si = faker.random_int(min=100000, max=9999999)
                sis.append(si)
                runners_data.append({
                    "name": ", ".join(faker.name().split(" ", 1)[::-1]),
                    "club": faker.company(),
                    "si": si,
                    "reg": f"{faker.lexify('???').upper()}{faker.numerify('####')}",
                    "call": "",
                    "startno": None,
                    "ocheck_processed": False,
                    "manual_dns": False,
                    "manual_disk": False,
                    "startlist_time": None,
                    "category_id": category_id
                })

            session.execute(Runner.__table__.insert(), runners_data)

            tzero = datetime.fromisoformat(api.get_basic_info(race_engine_file)["date_tzero"])

            punches_data = []
            for si in sis:
                start_time = tzero + timedelta(seconds=random.randint(0, 60))
                punches_data.append({"code": 1000, "si": si, "time": start_time})

                k = random.randint(1, num_controls)
                chosen_codes = [random.choice(control_codes) for _ in range(k)]

                last_time = start_time
                for code in chosen_codes:
                    last_time += timedelta(seconds=random.randint(10, 300))
                    punches_data.append({"code": int(code), "si": si, "time": last_time})

                finish_time = last_time + timedelta(seconds=random.randint(10, 300))
                punches_data.append({"code": 1001, "si": si, "time": finish_time})

            session.execute(Punch.__table__.insert(), punches_data)

            session.commit()

        class Cat:
            def __init__(self, name, id):
                self.name = name
                self.id = id

        return Cat(cat_name, category_id), num_runners, num_controls

    return _make


def test_python_and_rust_results(race_engine_file, race_with_results):
    """
    Test if python results and rust results match for the same randomized data.
    """
    gen_start = time.perf_counter()
    category, num_runners, num_controls = race_with_results(1000)
    gen_end = time.perf_counter()

    print(f"Generace: {gen_end - gen_start:.2f}s")

    rust_start = time.perf_counter_ns()
    res_rust = results.calculate_category(race_engine_file, category.name, False)
    rust_end = time.perf_counter_ns()
    print(f"Rust: {(rust_end - rust_start) / 1E6:.2f}ms")

    py_start = time.perf_counter_ns()
    res_py = py_calc_category(race_engine_file, category.name, False)
    py_end = time.perf_counter_ns()
    print(f"Python: {(py_end - py_start) / 1E6:.2f}ms")

    assert len(res_rust) == len(res_py)
    assert len(res_rust) == num_runners

    assert [(r.name, r.time, r.tx, r.status, r.place, r.order) for r in res_rust] == [
        (r.name, r.time, r.tx, r.status, r.place, r.order)
        for r in res_py]
