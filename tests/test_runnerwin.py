from unittest.mock import patch

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QInputDialog, QPushButton
from sqlalchemy import Select
from sqlalchemy.orm import Session

import api
import models
from ui.runnerwin import RunnerWindow


class DummyPL:
    def __init__(self):
        self.last = None

    def readout(self, si):
        self.last = si


class DummyReadoutWin:
    def __init__(self):
        self.printer = None
        self.last = None

    def print_readout(self, si, snura):
        self.last = (si, snura)


class FakeMW:
    def __init__(self, db):
        self.db = db
        self.pl = DummyPL()
        self.readout_win = DummyReadoutWin()


@pytest.fixture()
def in_memory_db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session as SASession

    engine = create_engine("sqlite:///:memory:", echo=False, future=True)
    models.Base.metadata.create_all(engine)

    with SASession(engine) as sess:
        cat = models.Category(name="M20", display_controls="")
        sess.add(cat)
        sess.commit()
        runner = models.Runner(
            name="Jiroutek, Jakub",
            club="Liberec",
            si=8514688,
            reg="ELB0904",
            call="",
            category=cat,
            startlist_time=None,
        )
        sess.add(runner)
        sess.commit()

    yield engine


@pytest.fixture()
def default_api_mocks():
    api.get_basic_info = lambda db: {"date_tzero": "2020-01-01T00:00:00", "band": "M2", "limit": 60}
    api.renumber_runners = lambda db: None
    api.get_registered_names = lambda: []
    api.get_registered_runners = lambda: []
    api.get_clubs = lambda: {}


@pytest.fixture()
def win(qtbot, in_memory_db, default_api_mocks):
    mw = FakeMW(in_memory_db)
    w = RunnerWindow(mw)
    qtbot.addWidget(w)
    w._show()
    yield w
    try:
        w.close()
        w.deleteLater()
    except Exception:
        pass


def _get_runner_by_name(engine, name):
    with Session(engine) as sess:
        return sess.scalars(Select(models.Runner).where(models.Runner.name == name)).one_or_none()


def find_button_by_tooltip(widget, substring):
    for btn in widget.findChildren(QPushButton):
        if substring in (btn.toolTip() or ""):
            return btn
    return None


def click_list_item(qtbot, list_widget, text):
    for i in range(list_widget.count()):
        item = list_widget.item(i)
        if item.text() == text:
            rect = list_widget.visualItemRect(item)
            center = rect.center()
            qtbot.mouseClick(list_widget.viewport(), Qt.LeftButton, pos=center)
            return
    pytest.fail(f"List item with text '{text}' not found")


def test_initial_population(win):
    categories = [win.category_edit.itemText(i) for i in range(win.category_edit.count())]
    assert "M20" in categories

    items = [win.runners_list.item(i).text() for i in range(win.runners_list.count())]
    assert "Jiroutek, Jakub" in items


def test_select_and_save(win, in_memory_db, qtbot):
    click_list_item(qtbot, win.runners_list, "Jiroutek, Jakub")

    win.name_edit.setText("Smith, Jane")
    win.SI_edit.setValue(456)

    save_btn = find_button_by_tooltip(win, "Uložit")
    assert save_btn is not None
    qtbot.mouseClick(save_btn, Qt.LeftButton)

    r = _get_runner_by_name(in_memory_db, "Smith, Jane")
    assert r is not None
    assert r.si == 456


def test_new_button_creates_blank_runner(win, in_memory_db, qtbot):
    new_btn = find_button_by_tooltip(win, "Nový")
    assert new_btn is not None
    qtbot.mouseClick(new_btn, Qt.LeftButton)

    items = [win.runners_list.item(i).text() for i in range(win.runners_list.count())]
    assert "" in items

    with Session(in_memory_db) as sess:
        blank = sess.scalars(Select(models.Runner).where(models.Runner.name == "")).one_or_none()
        assert blank is not None


def test_delete_button_removes_selected(win, in_memory_db, qtbot):
    click_list_item(qtbot, win.runners_list, "Jiroutek, Jakub")

    delete_btn = find_button_by_tooltip(win, "Smazat")
    assert delete_btn is not None
    qtbot.mouseClick(delete_btn, Qt.LeftButton)

    with Session(in_memory_db) as sess:
        r = sess.scalars(Select(models.Runner).where(models.Runner.name == "Jiroutek, Jakub")).one_or_none()
        assert r is None


def test_send_online_button_calls_pl_readout(win, qtbot):
    click_list_item(qtbot, win.runners_list, "Jiroutek, Jakub")

    send_btn = find_button_by_tooltip(win, "Odeslat online")
    assert send_btn is not None
    qtbot.mouseClick(send_btn, Qt.LeftButton)

    assert win.mw.pl.last == 8514688


def test_print_buttons_with_and_without_printer(win, qtbot):
    click_list_item(qtbot, win.runners_list, "Jiroutek, Jakub")

    print_btn = find_button_by_tooltip(win, "Vytisknout výčet")
    snura_btn = find_button_by_tooltip(win, "Vytisknout výčet na šňůru")
    assert print_btn is not None and snura_btn is not None

    win.mw.readout_win.printer = None
    qtbot.mouseClick(print_btn, Qt.LeftButton)
    assert win.mw.readout_win.last is None

    win.mw.readout_win.printer = object()
    qtbot.mouseClick(print_btn, Qt.LeftButton)
    assert win.mw.readout_win.last[0] == 8514688

    win.mw.readout_win.last = None
    qtbot.mouseClick(snura_btn, Qt.LeftButton)
    assert win.mw.readout_win.last == (8514688, True)


def test_set_starttime_dialog_applies_time(win, in_memory_db, qtbot):
    click_list_item(qtbot, win.runners_list, "Jiroutek, Jakub")

    st_btn = find_button_by_tooltip(win, "Změnit startovní čas")
    assert st_btn is not None

    with patch.object(QInputDialog, 'getDouble', return_value=(5.0, True)):
        qtbot.mouseClick(st_btn, Qt.LeftButton)

    with Session(in_memory_db) as sess:
        r = sess.get(models.Runner, win.selected)
        assert r.startlist_time is not None


def test_prefill_runner_from_completer(win, qtbot):
    api.get_registered_runners = lambda: [{"name": "New, Runner", "si": 9999999, "reg": "ELB9999"}]
    api.get_clubs = lambda: {"ELB": "Liberec"}

    win._prefill_runner("New, Runner")

    assert win.name_edit.text() == "New, Runner"
    assert win.SI_edit.value() == 9999999
    assert win.reg_edit.text() == "ELB9999"
    assert win.club_edit.text() == "Liberec"


def test_close_event_saves_changes(win, in_memory_db):
    win._select("Jiroutek, Jakub")
    win.name_edit.setText("Closed, Saved")

    win.close()
    with Session(in_memory_db) as sess:
        r = sess.scalars(Select(models.Runner).where(models.Runner.name == "Closed, Saved")).one_or_none()
        assert r is not None


def test_save_btn_helper_saves_name(win, in_memory_db, qtbot):
    click_list_item(qtbot, win.runners_list, "Jiroutek, Jakub")
    win.name_edit.setText("Helper, Saved")

    save_btn = find_button_by_tooltip(win, "Uložit")
    assert save_btn is not None
    qtbot.mouseClick(save_btn, Qt.LeftButton)

    with Session(in_memory_db) as sess:
        r = sess.scalars(Select(models.Runner).where(models.Runner.name == "Helper, Saved")).one_or_none()
        assert r is not None
