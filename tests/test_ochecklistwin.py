import json

import pytest
from PySide6.QtWidgets import QFileDialog
from sqlalchemy.orm import Session

import models
from ui.ochecklistwin import OCheckListWindow


def test_import_no_file_selected(mw, qtbot, monkeypatch):
    # Simulate user cancelling the file dialog
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: ("", ""))

    win = OCheckListWindow(mw)
    qtbot.addWidget(win)

    win._import()

    # No logs and nothing should change
    assert win.log.toPlainText().strip() == ""


def test_import_marks_dns_and_newcard(mw, session, make_category, qtbot, tmp_path, monkeypatch):
    # create a category and runners that will be updated
    cat = make_category()

    r = models.Runner(name="Alpha", club="C", si=123, reg="R1", call="", category=cat)
    session.add(r)
    session.commit()
    session.refresh(r)

    # create another runner already processed (should be skipped)
    r2 = models.Runner(name="Beta", club="C", si=456, reg="R2", call="", category=cat, ocheck_processed=True)
    session.add(r2)
    session.commit()
    session.refresh(r2)

    data = {
        "Data": [
            {"Runner": {"Id": str(r.id), "StartStatus": "DNS", "NewCard": 999}},
            {"Runner": {"Id": str(r2.id), "StartStatus": "DNS"}},
        ]
    }

    fn = tmp_path / "ocheck.yaml"
    fn.write_text(json.dumps(data))

    # Note: the code uses yaml.load with a Loader; write YAML so load works.
    # We'll convert the JSON we wrote into valid YAML form by re-writing using yaml.safe_dump if available.
    try:
        import yaml

        yaml.safe_dump(data, fn.open("w"))
    except Exception:
        # fallback: file already contains JSON which yaml.load can parse as well
        pass

    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(fn), ""))

    win = OCheckListWindow(mw)
    qtbot.addWidget(win)

    win._import()

    # check log contains both DNS and SI change message for runner r
    txt = win.log.toPlainText()
    assert f"{r.name}: DNS" in txt
    assert f"{r.name}: SI {r.si} => 999" in txt

    # verify DB changes: manual_dns set for r, r2 unchanged
    with Session(mw.db) as s:
        rr = s.get(models.Runner, r.id)
        rr2 = s.get(models.Runner, r2.id)
        assert rr.manual_dns is True
        assert rr2.manual_dns is False


def test_import_skips_processed(mw, session, make_category, qtbot, tmp_path, monkeypatch):
    # create a category and a runner already processed
    cat = make_category()
    r = models.Runner(name="Processed", club="C", si=777, reg="R3", call="", category=cat, ocheck_processed=True)
    session.add(r)
    session.commit()
    session.refresh(r)

    data = {"Data": [{"Runner": {"Id": str(r.id), "StartStatus": "DNS"}}]}

    fn = tmp_path / "ocheck2.yaml"
    try:
        import yaml

        yaml.safe_dump(data, fn.open("w"))
    except Exception:
        fn.write_text(str(data))

    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(fn), ""))

    win = OCheckListWindow(mw)
    qtbot.addWidget(win)

    win._import()

    assert win.log.toPlainText().strip() == ""


def test_import_malformed_yaml_raises(mw, qtbot, tmp_path, monkeypatch):
    fn = tmp_path / "bad.yaml"
    fn.write_text("::: this is not valid yaml ::::")

    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(fn), ""))

    win = OCheckListWindow(mw)
    qtbot.addWidget(win)

    with pytest.raises(Exception):
        win._import()


def test_import_missing_id_raises_keyerror(mw, qtbot, tmp_path, monkeypatch):
    data = {"Data": [{"Runner": {"StartStatus": "DNS"}}]}
    fn = tmp_path / "missing_id.yaml"
    try:
        import yaml

        yaml.safe_dump(data, fn.open("w"))
    except Exception:
        fn.write_text(json.dumps(data))

    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(fn), ""))

    win = OCheckListWindow(mw)
    qtbot.addWidget(win)

    with pytest.raises(KeyError):
        win._import()


def test_import_unsupported_startstatus_is_skipped(mw, session, make_category, qtbot, tmp_path, monkeypatch):
    cat = make_category()
    r = models.Runner(name="Gamma", club="C", si=321, reg="R4", call="", category=cat)
    session.add(r)
    session.commit()
    session.refresh(r)

    data = {"Data": [{"Runner": {"Id": str(r.id), "StartStatus": "OK"}}]}
    fn = tmp_path / "unsupported.yaml"
    try:
        import yaml

        yaml.safe_dump(data, fn.open("w"))
    except Exception:
        fn.write_text(json.dumps(data))

    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (str(fn), ""))

    win = OCheckListWindow(mw)
    qtbot.addWidget(win)

    win._import()

    assert win.log.toPlainText().strip() == ""
    with Session(mw.db) as s:
        rr = s.get(models.Runner, r.id)
        assert rr.manual_dns is False
