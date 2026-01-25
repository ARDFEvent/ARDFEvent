import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolButton
from sqlalchemy import create_engine

import api
from models import Base
from ui.mainwin import MainWindow, RaceWindow


@pytest.fixture(autouse=True)
def patch_basic_info(monkeypatch):
    monkeypatch.setattr(api, "get_basic_info", lambda db: {
        "name": "TestRace",
        "date_tzero": "2025-01-01T10:00:00",
        "organizer": "",
        "limit": "60",
        "band": "80m",
    })
    yield


def test_sidebar_buttons_exist_and_switch_pages(qtbot, tmp_path):
    dbfile = tmp_path / "test_mainwin.db"
    Base.metadata.create_all(create_engine(f"sqlite:///{dbfile}"))
    win = RaceWindow(f"sqlite:///{dbfile}")
    qtbot.addWidget(win)
    qtbot.waitExposed(win)

    buttons = [b for b in win.sidebar.findChildren(QToolButton)]
    assert len(buttons) >= 2

    btn = buttons[1]
    qtbot.mouseClick(btn, Qt.LeftButton)

    assert win.stack.currentIndex() == 1


def test_close_hides_window(qtbot, tmp_path):
    win = MainWindow()
    qtbot.addWidget(win)
    dbfile = tmp_path / "test_mainwin.db"
    Base.metadata.create_all(create_engine(f"sqlite:///{dbfile}"))
    win.show(f"sqlite:///{dbfile}")
    qtbot.waitExposed(win)

    win.close()
    assert not win.isVisible()
