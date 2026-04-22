import sys
import types
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

import api
import models

pytest_plugins = ["src"] # Add this line

# --- Database & Core Fixtures ---

@pytest.fixture(scope="function")
def engine():
    """Provide an in-memory SQLite engine with tables created."""
    engine = create_engine("sqlite:///:memory:", future=True)
    models.Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


def gen_race(eng, faker):
    """Helper to populate races basicinfo."""
    dtzero = faker.date_time_this_decade()
    payload = {
        "name": " ".join([faker.word() for _ in range(5)]),
        "date_tzero": dtzero.isoformat(),
        "organizer": faker.company(),
        "limit": str(faker.random_int(10, 180)),
        "band": "2m",
    }
    api.set_basic_info(eng, payload)


@pytest.fixture(scope="function")
def race_engine(engine, faker):
    """Provide an in-memory SQLite engine pre-populated with a races basicinfo."""
    gen_race(engine, faker)
    yield engine


@pytest.fixture(scope="function")
def race_engine_file(faker, tmp_path):
    """Provide a file SQLite engine pre-populated with a races basicinfo."""
    dbfile = tmp_path / "AEtest.db"
    eng = create_engine(f"sqlite:///{dbfile}")
    models.Base.metadata.create_all(eng)
    gen_race(eng, faker)
    yield eng
    eng.dispose()


@pytest.fixture(scope="function")
def session(engine):
    """Provide a SQLAlchemy Session bound to the engine."""
    with Session(bind=engine) as sess:
        yield sess


@pytest.fixture(scope="function")
def file_session(race_engine_file):
    """Provide a SQLAlchemy Session bound to the file-based engine."""
    with Session(bind=race_engine_file) as sess:
        yield sess


# --- Mock Window Objects ---

class DummyMainWin:
    """A mock main window that holds the database engine."""

    def __init__(self, engine):
        self.db = engine


@pytest.fixture()
def mw(engine):
    """Fixture for the class-based mock window."""
    return DummyMainWin(engine)


@pytest.fixture()
def fake_mw(engine):
    """Fixture for a lightweight namespace-based mock window."""
    ns = types.SimpleNamespace()
    ns.db = engine
    return ns


# --- Randomized Model Factories ---

@pytest.fixture()
def make_category(session, faker):
    """Factory to create Category rows with unique random names."""

    def _make(name=None, controls=None, sess=None):
        if sess is None:
            sess = session
        c = models.Category(
            name=name or f"Cat-{faker.random_int(1, 99)}",
            controls=controls or [],
            display_controls=""
        )
        sess.add(c)
        sess.commit()
        return c

    return _make


@pytest.fixture()
def make_control(session, faker):
    """Factory to create Control rows with randomized location and codes."""

    def _make(name=None, code=None, mandatory=False, spectator=False, lat=None, lon=None, sess=None):
        if sess is None:
            sess = session
        ctrl = models.Control(
            name=name or f"{faker.random_int(1, 99)}",
            code=code or faker.random_int(min=31, max=999),
            mandatory=mandatory,
            spectator=spectator,
            lat=lat or float(faker.latitude()),
            lon=lon or float(faker.longitude())
        )
        sess.add(ctrl)
        sess.commit()
        return ctrl

    return _make


@pytest.fixture()
def make_runner(session, make_category, faker):
    """Factory to create Runner rows with realistic random persona data."""

    def _make(**kwargs):
        if "sess" not in kwargs.keys():
            sess = session
        else:
            sess = kwargs.pop("sess")
        defaults = {
            "name": ", ".join(faker.name().split(" ", 1)[::-1]),
            "club": faker.company(),
            "si": faker.random_int(min=100000, max=9999999),
            "reg": f"{faker.lexify('???').upper()}{faker.numerify('####')}",
            "call": "",
            "startno": None,
            "ocheck_processed": False,
            "manual_dns": False,
            "manual_disk": False,
            "startlist_time": None
        }

        data = {**defaults, **kwargs}

        if "category" not in data or data["category"] is None:
            data["category"] = make_category()

        runner = models.Runner(
            name=data["name"],
            club=data["club"],
            si=data["si"],
            reg=data["reg"],
            call=data["call"],
            startno=data["startno"],
            startlist_time=data["startlist_time"],
            category_id=data["category"].id,
            ocheck_processed=data["ocheck_processed"],
            manual_dns=data["manual_dns"],
            manual_disk=data["manual_disk"]
        )

        sess.add(runner)
        sess.commit()
        return runner

    return _make
