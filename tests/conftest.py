import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine

# ensure src is importable like other tests
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

from models import Base


@pytest.fixture(scope="function")
def engine():
    """Provide an in-memory SQLite engine with tables created."""
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    yield engine
    try:
        engine.dispose()
    except Exception:
        pass


# New shared fixtures and helpers extracted for tests
from sqlalchemy.orm import Session
import types
import models


@pytest.fixture(scope="function")
def session(engine):
    """Provide a SQLAlchemy Session bound to the engine."""
    sess = Session(bind=engine)
    yield sess
    try:
        sess.close()
    except Exception:
        pass


class DummyMainWin:
    def __init__(self, engine):
        self.db = engine


@pytest.fixture()
def mw(engine):
    """A simple main-window-like object with a db attribute."""
    return DummyMainWin(engine)


@pytest.fixture()
def fake_mw(engine):
    """A lightweight main-window namespace used by some tests."""
    ns = types.SimpleNamespace()
    ns.db = engine
    return ns


@pytest.fixture()
def make_category(session):
    """Factory to quickly create Category rows in tests."""

    def _make(name="C1", display_controls=""):
        c = models.Category(name=name, controls=[], display_controls=display_controls)
        session.add(c)
        session.commit()
        session.refresh(c)
        return c

    return _make


@pytest.fixture()
def make_control(session):
    """Factory to quickly create Control rows in tests."""

    def _make(name="Ctrl1", code=1, mandatory=False, spectator=False, lat=None, lon=None):
        ctrl = models.Control(name=name, code=code, mandatory=mandatory, spectator=spectator, lat=lat, lon=lon)
        session.add(ctrl)
        session.commit()
        session.refresh(ctrl)
        return ctrl

    return _make

# Note: the custom minimal `qtbot` fixture was removed so the real `qtbot` from pytest-qt
# will be used by tests. Ensure pytest-qt is installed in your test environment.
