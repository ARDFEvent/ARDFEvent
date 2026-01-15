from datetime import datetime

import pytest
from PySide6.QtCore import Qt

import api
from ui.basicinfowin import BasicInfoWindow


@pytest.fixture()
def basic_win(qtbot, monkeypatch, mw):
    mw.db = "DB"

    monkeypatch.setattr(api, "set_basic_info", lambda db, info: None)

    win = BasicInfoWindow(mw)
    qtbot.addWidget(win)
    yield win
    try:
        win.close()
        win.deleteLater()
    except Exception:
        pass


def test_show_populates_fields(basic_win, monkeypatch):
    payload = {
        "name": "Testový závod",
        "date_tzero": "2025-05-10T09:30:00",
        "organizer": "Pořadatel",
        "limit": "120",
        "band": "2m",
    }

    monkeypatch.setattr(api, "get_basic_info", lambda db: payload)

    basic_win._show()

    assert basic_win.name_edit.text() == "Testový závod"

    dt = basic_win.date_edit.dateTime().toPython()
    assert dt.year == 2025 and dt.month == 5 and dt.day == 10 and dt.hour == 9 and dt.minute == 30
    assert basic_win.org_edit.text() == "Pořadatel"
    assert basic_win.limit_edit.value() == 120
    assert basic_win.band_select.currentText() == "2m"


def test_save_calls_api_with_expected_structure(basic_win, monkeypatch, qtbot):
    called = {}

    def fake_set_basic_info(db, info):
        called['db'] = db
        called['info'] = info

    monkeypatch.setattr(api, "set_basic_info", fake_set_basic_info)

    qtbot.keyClicks(basic_win.name_edit, "Ulozeny zavod")
    qtbot.keyClick(basic_win.name_edit, Qt.Key_Tab)

    qtbot.keyClicks(basic_win.org_edit, "Poradatel 2")
    qtbot.keyClick(basic_win.org_edit, Qt.Key_Tab)

    basic_win.date_edit.setDateTime(datetime(2023, 7, 4, 14, 5, 9))
    qtbot.keyClick(basic_win.date_edit, Qt.Key_Tab)

    basic_win.limit_edit.setValue(45)
    qtbot.keyClick(basic_win.limit_edit, Qt.Key_Tab)

    basic_win.band_select.setCurrentIndex(1)

    qtbot.wait(50)

    assert called.get('db') == "DB"
    info = called.get('info')
    assert info is not None

    assert info['name'] == "Ulozeny zavod"
    assert info['organizer'] == "Poradatel 2"
    assert info['date_tzero'] == datetime(2023, 7, 4, 14, 5, 0).isoformat()
    assert info['limit'] == "45"
    assert info['band'] == "80m"
