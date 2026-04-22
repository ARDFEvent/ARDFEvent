import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton
from sqlalchemy import select

from models import Control
from ui.controlswin import ControlsWindow


def find_button_by_tooltip(widget, substring):
    for btn in widget.findChildren(QPushButton):
        if substring in (btn.toolTip() or "") or substring in (btn.text() or ""):
            return btn
    return None


def click_table_row(qtbot, table, row):
    rect = table.visualItemRect(table.item(row, 0))
    center = rect.center()
    qtbot.mouseClick(table.viewport(), Qt.LeftButton, pos=center)


def test_preset_all_applies_to_db(qtbot, fake_mw):
    win = ControlsWindow(fake_mw)
    qtbot.addWidget(win)

    all_btn = find_button_by_tooltip(win, "R1")
    assert all_btn is not None
    qtbot.mouseClick(all_btn, Qt.LeftButton)

    from sqlalchemy.orm import Session

    with Session(fake_mw.db) as sess:
        rows = sess.scalars(select(Control)).all()

    names = [r.name for r in rows]
    assert "1" in names
    assert "R1" in names
    assert "M" in names


def test_add_edit_save_cycle(qtbot, fake_mw, faker):
    win = ControlsWindow(fake_mw)
    qtbot.addWidget(win)

    add_btn = find_button_by_tooltip(win, "Přidat")
    assert add_btn is not None
    qtbot.mouseClick(add_btn, Qt.LeftButton)

    name = faker.word()
    code = faker.random_int(min=31, max=999)
    lat = float(faker.latitude())
    lon = float(faker.longitude())

    win.table.item(0, 0).setText(name)
    win.table.item(0, 1).setText(str(code))

    win.table.item(0, 2).setCheckState(Qt.CheckState.Checked)
    win.table.item(0, 3).setCheckState(Qt.CheckState.Checked)

    win.table.item(0, 4).setText(str(lat))
    win.table.item(0, 5).setText(str(lon))

    save_btn = find_button_by_tooltip(win, "Uložit")
    assert save_btn is not None
    qtbot.mouseClick(save_btn, Qt.LeftButton)

    from sqlalchemy.orm import Session

    with Session(fake_mw.db) as sess:
        rows = sess.scalars(select(Control)).all()

    assert len(rows) == 1
    c = rows[0]
    assert c.name == name
    assert c.code == code
    
    assert c.mandatory is True
    assert c.spectator is True
    assert c.lat == pytest.approx(lat, abs=0.001)
    assert c.lon == pytest.approx(lon, abs=0.001)
