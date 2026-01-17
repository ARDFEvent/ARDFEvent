import csv

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFileDialog, QPushButton
from sqlalchemy import Select
from sqlalchemy.orm import Session

import api
from models import Runner, Category
from ui.importwin import ImportWindow


class DummyRunner:
    def __init__(self, name, reg, category_name):
        self.name = name
        self.reg = reg
        self.category_name = category_name


def find_button_by_text(widget, substring):
    for btn in widget.findChildren(QPushButton):
        if substring in (btn.text() or ""):
            return btn
    return None


def test_select_file_cancelled(qtbot, mw, monkeypatch):
    monkeypatch.setattr(QFileDialog, 'getOpenFileName', lambda *args, **kwargs: ('', ''))

    win = ImportWindow(mw)
    qtbot.addWidget(win)

    file_btn = find_button_by_text(win, "Vyberte soubor")
    assert file_btn is not None
    qtbot.mouseClick(file_btn, Qt.LeftButton)

    assert win.log.toPlainText() == ''


def test_select_file_imports_and_logs(tmp_path, qtbot, mw, monkeypatch):
    csv_path = tmp_path / 'runners.csv'
    rows = [
        ['Jméno', 'Příjmení', 'Registrace', 'SI', 'Kategorie'],
        ['Jakub', 'Jiroutek', 'ELB0904', '8514688', 'M20'],
        ['Test', 'Testový', 'FPA8206', '428206', 'M20'],
        ['Test', 'Testová', 'ELB8451', '428208', 'D20'],
        ['Test', 'Testová', 'ELB8451', '428207', 'D20'],
    ]
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerows(rows)

    monkeypatch.setattr(QFileDialog, 'getOpenFileName', lambda *args, **kwargs: (str(csv_path), ''))

    monkeypatch.setattr(api, 'get_clubs', lambda: {'ELB': 'Liberec'})

    win = ImportWindow(mw)
    qtbot.addWidget(win)

    file_btn = find_button_by_text(win, "Vyberte soubor")
    assert file_btn is not None
    qtbot.mouseClick(file_btn, Qt.LeftButton)

    with Session(mw.db) as sess:
        tested = []
        for row in rows[1:][::-1]:
            if row[2] in tested:
                continue
            runner = sess.scalars(Select(Runner).where(Runner.name == f"{row[1]}, {row[0]}")).one_or_none()
            assert runner is not None
            assert runner.reg == row[2]
            assert runner.si == int(row[3])
            category = sess.get(Category, runner.category_id)
            assert category.name == row[4]
            tested.append(row[2])

    text = win.log.toPlainText()
    assert f"Načten soubor {tmp_path / 'runners.csv'}. Počet závodníků: 4." in text
    assert "OK: Závodník Jiroutek, Jakub byl úspěšně importován." in text
    assert "/!\\ WAR: Závodník Testový, Test nemá platný klub FPA. Přesto se importuje." in text
    assert "/!\\ WAR: Pro závodníka Testová, Test nebyla nalezena kategorie D20! Kategorie vytvořena." in text
    assert "/!\\ WAR: Závodník Testová, Test s registračním číslem ELB8451 již existuje! Přepisuje se." in text
