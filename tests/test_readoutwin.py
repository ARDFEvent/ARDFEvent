from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from PySide6.QtWidgets import QDialog, QLineEdit, QMessageBox, QCompleter
from escpos.printer import Dummy
from sqlalchemy import Select
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import api
import models
import results
from models import Base
from ui.readoutwin import ReadoutWindow, PrinterOptions


class FakeDialog:
    def __init__(self, *args, **kwargs):
        self._text = ""

    def setWindowTitle(self, *a, **k):
        pass

    def setLabelText(self, *a, **k):
        pass

    def setTextValue(self, v):
        self._text = v

    def findChild(self, cls):
        return QLineEdit()

    def exec(self):
        return QDialog.Accepted

    def textValue(self):
        return "Existing"


class FakeCompleter(QCompleter):
    def __init__(self, completions, parent=None, **kwargs):
        super().__init__(list(completions))

    def setCaseSensitivity(self, cs):
        super().setCaseSensitivity(cs)


def make_mw(engine):
    mw = SimpleNamespace()
    mw.db = engine
    mw.results_win = SimpleNamespace(_update_results=lambda: None)
    mw.inforest_win = SimpleNamespace(_update=lambda: None)
    mw.pl = SimpleNamespace(readout=lambda si: None)
    return mw


def _create_engine_db(tmp_path: Path):
    dbfile = tmp_path / "test_readout.db"
    engine = create_engine(f"sqlite:///{dbfile}", future=True)
    Base.metadata.create_all(engine)
    return engine


def test_handle_readout_assigns_runner_via_input_dialog(tmp_path, make_category, qtbot, monkeypatch):
    engine = _create_engine_db(tmp_path)
    with Session(engine) as s:
        cat = models.Category(name="C1", display_controls="") if not make_category else None
    with Session(engine) as s:
        cat = models.Category(name="C1", display_controls="")
        s.add(cat)
        s.commit()
        s.refresh(cat)
        runner = models.Runner(name="Existing", club="C", si=0, reg="R1", call="", category=cat)
        s.add(runner)
        s.commit()
        s.refresh(runner)
        runner_id = runner.id

    rmw = make_mw(engine)
    win = ReadoutWindow(rmw)
    qtbot.addWidget(win)

    si_no = 123456
    punch_time = datetime.now().replace(microsecond=0)

    data = {
        "card_number": si_no,
        "punches": [[1, punch_time]],
        "start": None,
        "finish": None,
    }

    monkeypatch.setattr('ui.readoutwin.QInputDialog', FakeDialog)
    monkeypatch.setattr('ui.readoutwin.QCompleter', FakeCompleter)

    win._handle_readout(data)

    with Session(engine) as s:
        rdb = s.get(models.Runner, runner_id)
        assert rdb.si == si_no


def test_handle_readout_overwrite_existing_punch_yes(tmp_path, make_category, qtbot, monkeypatch):
    engine = _create_engine_db(tmp_path)
    with Session(engine) as s:
        cat = models.Category(name="C1", display_controls="")
        s.add(cat)
        s.commit()
        s.refresh(cat)
        si_no = 222333
        runner = models.Runner(name="Runner1", club="C", si=si_no, reg="R2", call="", category=cat)
        s.add(runner)
        s.commit()
        s.refresh(runner)
        old_punch = models.Punch(si=si_no, code=5, time=datetime.now().replace(microsecond=0))
        s.add(old_punch)
        s.commit()

    rmw = make_mw(engine)
    win = ReadoutWindow(rmw)
    qtbot.addWidget(win)

    punch_time = datetime.now().replace(microsecond=0)
    data = {"card_number": si_no, "punches": [[7, punch_time], [8, punch_time]], "start": None, "finish": None}

    monkeypatch.setattr('ui.readoutwin.QMessageBox.warning', lambda *a, **k: QMessageBox.StandardButton.Yes,
                        raising=False)

    win._handle_readout(data)

    txt = win.log.toPlainText()
    assert "Přeps" in txt or "Přeps".lower() in txt.lower()

    with Session(engine) as s:
        punches = s.scalars(Select(models.Punch).where(models.Punch.si == si_no)).all()
        assert len(punches) >= 1


def test_print_readout_produces_output_and_calls_helpers(tmp_path, make_category, qtbot, monkeypatch):
    engine = _create_engine_db(tmp_path)
    with Session(engine) as s:
        cat = models.Category(name="C1", display_controls="")
        s.add(cat)
        s.commit()
        s.refresh(cat)
        si_no = 555666
        runner = models.Runner(name="PrintMe", club="Club", si=si_no, reg="R3", call="", category=cat)
        s.add(runner)
        s.commit()
        s.refresh(runner)

    monkeypatch.setattr(api, "get_basic_info", lambda db: {"name": "RaceX", "date_tzero": "2025-01-01T10:00:00"})

    res_obj = SimpleNamespace(name="PrintMe", time=100, tx=0, status="OK", place=1)
    monkeypatch.setattr(results, "calculate_category", lambda db, catname: [res_obj])

    rmw = make_mw(engine)
    called = {"results": False, "inforest": False, "readout": False}
    rmw.results_win = SimpleNamespace(_update_results=lambda: called.__setitem__("results", True))
    rmw.inforest_win = SimpleNamespace(_update=lambda: called.__setitem__("inforest", True))
    rmw.pl = SimpleNamespace(readout=lambda si: called.__setitem__("readout", si))

    win = ReadoutWindow(rmw)
    qtbot.addWidget(win)

    win.printer = Dummy()
    win.printer_optns = PrinterOptions(paper=True, title=True, feed=1, cut=False, logo=None, link=False, qr=False)

    data = {"card_number": si_no, "punches": [], "start": None, "finish": None}

    monkeypatch.setattr('ui.readoutwin.QMessageBox.warning', lambda *a, **k: QMessageBox.StandardButton.Yes,
                        raising=False)
    monkeypatch.setattr('ui.readoutwin.QCompleter', FakeCompleter)
    monkeypatch.setattr('ui.readoutwin.QInputDialog', FakeDialog)

    win._handle_readout(data)

    assert called["readout"] == si_no
    out = getattr(win.printer, "output", None)
    assert out is not None


def test_handle_readout_nonexistent_si_user_cancels(tmp_path, qtbot, monkeypatch):
    engine = _create_engine_db(tmp_path)
    rmw = make_mw(engine)
    win = ReadoutWindow(rmw)
    qtbot.addWidget(win)

    si_no = 999999
    data = {"card_number": si_no, "punches": [], "start": None, "finish": None}

    class CancelDialog(FakeDialog):
        def exec(self):
            return QDialog.Rejected

        def textValue(self):
            return ""

    monkeypatch.setattr('ui.readoutwin.QInputDialog', CancelDialog)
    monkeypatch.setattr('ui.readoutwin.QCompleter', FakeCompleter)

    win._handle_readout(data)

    assert "není ale přiřazen" in win.log.toPlainText().lower()


def test_handle_readout_nonexistent_si_name_not_found(tmp_path, qtbot, monkeypatch):
    engine = _create_engine_db(tmp_path)
    with Session(engine) as s:
        cat = models.Category(name="C1", display_controls="")
        s.add(cat)
        s.commit()
        s.refresh(cat)
        r = models.Runner(name="Someone", club="Club", si=111111, reg="R1", call="", category=cat)
        s.add(r)
        s.commit()

    rmw = make_mw(engine)
    win = ReadoutWindow(rmw)
    qtbot.addWidget(win)

    si_no = 888888
    data = {"card_number": si_no, "punches": [], "start": None, "finish": None}

    class BadNameDialog(FakeDialog):
        def exec(self):
            return QDialog.Accepted

        def textValue(self):
            return "NoSuchName"

    monkeypatch.setattr('ui.readoutwin.QInputDialog', BadNameDialog)
    monkeypatch.setattr('ui.readoutwin.QCompleter', FakeCompleter)

    win._handle_readout(data)

    assert "nenalezen" in win.log.toPlainText().lower() or "nenalezeno" in win.log.toPlainText().lower()
