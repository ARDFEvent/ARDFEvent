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


def test_show_populates_fields(engine, basic_win, monkeypatch, faker):
    dtzero = faker.date_time_this_decade()
    payload = {
        "name": " ".join([faker.word() for _ in range(5)]),
        "date_tzero": dtzero.isoformat(),
        "organizer": faker.company(),
        "limit": str(faker.random_int(10, 180)),
        "band": "2m",
    }

    monkeypatch.setattr(api, "get_basic_info", lambda db: payload)

    basic_win._show()

    assert basic_win.name_edit.text() == payload["name"]

    dt = basic_win.date_edit.dateTime().toPython()
    assert dt.year == dtzero.year and dt.month == dtzero.month and dt.day == dtzero.day and dt.hour == dtzero.hour and dt.minute == dtzero.minute
    assert basic_win.org_edit.text() == payload["organizer"]
    assert basic_win.limit_edit.value() == int(payload["limit"])
    assert basic_win.band_select.currentText() == "2m"


def test_save_calls_api_with_expected_structure(basic_win, monkeypatch, qtbot, faker):
    called = {}
    
    # Generate random test data
    name = faker.company()
    org = faker.company()
    dt = faker.date_time_this_year().replace(second=0, microsecond=0)
    limit = faker.random_int(10, 180)
    
    def fake_set_basic_info(db, info):
        called['db'] = db
        called['info'] = info

    monkeypatch.setattr(api, "set_basic_info", fake_set_basic_info)

    qtbot.keyClicks(basic_win.name_edit, name)
    qtbot.keyClick(basic_win.name_edit, Qt.Key_Tab)

    qtbot.keyClicks(basic_win.org_edit, org)
    qtbot.keyClick(basic_win.org_edit, Qt.Key_Tab)

    basic_win.date_edit.setDateTime(dt)
    qtbot.keyClick(basic_win.date_edit, Qt.Key_Tab)

    basic_win.limit_edit.setValue(limit)
    qtbot.keyClick(basic_win.limit_edit, Qt.Key_Tab)

    # Randomly select a band index (0 or 1 usually)
    idx = faker.random_int(0, 1)
    basic_win.band_select.setCurrentIndex(idx)
    expected_band = basic_win.band_select.itemText(idx)

    qtbot.wait(50)
    basic_win._save()
    
    assert called.get('db') == "DB"
    info = called.get('info')
    assert info is not None

    assert info['name'] == name
    assert info['organizer'] == org
    assert info['date_tzero'] == dt.isoformat()
    assert info['limit'] == str(limit)
    assert info['band'] == expected_band
