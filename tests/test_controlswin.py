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


def test_add_edit_save_cycle(qtbot, fake_mw):
    win = ControlsWindow(fake_mw)
    qtbot.addWidget(win)

    add_btn = find_button_by_tooltip(win, "Přidat")
    assert add_btn is not None
    qtbot.mouseClick(add_btn, Qt.LeftButton)

    win.table.item(0, 0).setText("X")
    win.table.item(0, 1).setText("123")

    win.table.item(0, 2).setCheckState(Qt.CheckState.Checked)
    win.table.item(0, 3).setCheckState(Qt.CheckState.Checked)

    win.table.item(0, 4).setText("12.34")
    win.table.item(0, 5).setText("56.78")

    save_btn = find_button_by_tooltip(win, "Uložit")
    assert save_btn is not None
    qtbot.mouseClick(save_btn, Qt.LeftButton)

    from sqlalchemy.orm import Session

    with Session(fake_mw.db) as sess:
        rows = sess.scalars(select(Control)).all()

    assert len(rows) == 1
    c = rows[0]
    assert c.name == "X"
    assert c.code == 123
    
    assert c.mandatory is True
    assert c.spectator is True
    assert c.lat == pytest.approx(12.34)
    assert c.lon == pytest.approx(56.78)
