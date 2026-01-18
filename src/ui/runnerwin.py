import time
from datetime import timedelta

from escpos.printer import Serial
from PySide6.QtCore import QStringListModel, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QCompleter,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)
from serial.tools.list_ports import comports
from sqlalchemy import Delete, Select
from sqlalchemy.orm import Session

import api
from models import Category, Runner
from ui.readoutwin import print_readout


class RunnerWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        sess = Session(self.mw.db)

        mainlay = QHBoxLayout()
        self.setLayout(mainlay)

        leftlay = QVBoxLayout()
        mainlay.addLayout(leftlay)

        new_btn = QPushButton("Nový")
        new_btn.clicked.connect(self._new_runner)
        leftlay.addWidget(new_btn)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Hledat")
        self.search.textEdited.connect(self._update_runners_cats)
        leftlay.addWidget(self.search)

        self.runners_list = QListWidget()
        self.runners_list.itemClicked.connect(self._select_by_user)
        leftlay.addWidget(self.runners_list)

        right_lay = QVBoxLayout()
        mainlay.addLayout(right_lay)

        details_lay = QFormLayout()
        right_lay.addLayout(details_lay)

        self.name_edit = QLineEdit()
        self.name_edit.textEdited.connect(self._save_runner)

        details_lay.addRow("Jméno", self.name_edit)

        self.name_completer = QCompleter([])
        self.name_completer.highlighted.connect(self._prefill_runner)
        self.name_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.name_edit.setCompleter(self.name_completer)

        self.club_edit = QLineEdit()
        details_lay.addRow("Klub", self.club_edit)

        self.SI_edit = QSpinBox()
        self.SI_edit.setMaximum(10_000_000)
        details_lay.addRow("SI", self.SI_edit)

        self.reg_edit = QLineEdit()
        details_lay.addRow("Reg. číslo", self.reg_edit)

        self.call_edit = QLineEdit()
        details_lay.addRow("Volačka", self.call_edit)

        self.category_edit = QComboBox()
        details_lay.addRow("Kategorie", self.category_edit)

        self.starttime_edit = QTimeEdit()
        self.starttime_edit.setDisplayFormat("HH:mm:ss")
        details_lay.addRow("Start dle startovky", self.starttime_edit)

        self.dns_edit = QCheckBox()
        details_lay.addRow("DNS", self.dns_edit)

        self.dsq_edit = QCheckBox()
        details_lay.addRow("DSQ", self.dsq_edit)

        save_btn = QPushButton("Uložit")
        save_btn.clicked.connect(self._save_runner)
        details_lay.addWidget(save_btn)

        print_btn = QPushButton("Vytisknout výčet")
        print_btn.clicked.connect(self._print_readout)
        details_lay.addWidget(print_btn)

        delete_btn = QPushButton("Smazat")
        delete_btn.clicked.connect(self._delete_runner)
        details_lay.addWidget(delete_btn)

        self.selected = 0
        self.category_indexes = {}

        sess.close()

    def _prefill_runner(self, text):
        registration = api.get_registered_runners()
        runner = list(filter(lambda r: r["name"] == text, registration))
        if runner:
            runner = runner[0]
            self.name_edit.setText(runner["name"])
            self.SI_edit.setValue(runner["si"])
            self.reg_edit.setText(runner["reg"])
            self.club_edit.setText(api.get_clubs().get(runner["reg"][:3], ""))
            self._save_runner()

    def _get_runner(self, sess: Session):
        return sess.scalars(
            Select(Runner).where(Runner.id == self.selected)
        ).one_or_none()

    def _save_btn(self):
        self._select_by_user(QListWidgetItem(self.name_edit.text()))

    def _save_runner(self):
        sess = Session(self.mw.db)
        runner = self._get_runner(sess)
        if runner:
            runner.name = self.name_edit.text()
            runner.club = self.club_edit.text()
            runner.si = self.SI_edit.text()
            runner.reg = self.reg_edit.text()
            runner.call = self.call_edit.text()
            if self.starttime_edit.isEnabled():
                runner.startlist_time = (
                    self.starttime_edit.dateTime().toPython().astimezone()
                )
            runner.category = sess.scalars(
                Select(Category).where(
                    Category.name == self.category_edit.currentText()
                )
            ).one()
            runner.manual_dns = self.dns_edit.isChecked()
            runner.manual_disk = self.dsq_edit.isChecked()

        sess.commit()
        sess.close()

        self._update_runners_cats()

    def _select_by_user(self, item: QListWidgetItem):
        text = item.text()
        self._save_runner()
        self._update_runners_cats()
        self._select(text)

    def _select(self, text):
        sess = Session(self.mw.db)
        runner = sess.scalars(Select(Runner).where(Runner.name == text)).one_or_none()

        if runner:
            self.name_edit.setText(runner.name)
            self.club_edit.setText(runner.club)
            self.SI_edit.setValue(runner.si)
            self.reg_edit.setText(runner.reg)
            self.call_edit.setText(runner.call)
            if runner.startlist_time:
                self.starttime_edit.setDisabled(False)
                self.starttime_edit.setDateTime(
                    runner.startlist_time
                    + timedelta(seconds=-time.timezone)
                    + timedelta(hours=(1 if time.daylight else 0))
                )
            else:
                self.starttime_edit.setDisabled(True)

            self.category_edit.setCurrentIndex(
                self.category_indexes[runner.category.name]
            )

            self.dns_edit.setChecked(runner.manual_dns)
            self.dsq_edit.setChecked(runner.manual_disk)

            self.selected = runner.id
        else:
            raise ValueError("Runner not found")
        sess.close()

    def _update_runners_cats(self):
        self.runners_list.clear()

        cat_index = self.category_edit.currentIndex()
        self.category_edit.clear()

        sess = Session(self.mw.db)
        api.renumber_runners(self.mw.db)

        runners = sess.scalars(
            Select(Runner)
            .where(Runner.name.icontains(self.search.text()))
            .order_by(Runner.name.asc())
        ).all()
        for runner in runners:
            self.runners_list.addItem(QListWidgetItem(runner.name))

        i = 0
        categories = sess.scalars(Select(Category).order_by(Category.name.asc())).all()
        for category in categories:
            self.category_edit.addItem(category.name)
            self.category_indexes[category.name] = i
            i += 1

        self.category_edit.setCurrentIndex(cat_index)

        runners = sess.scalars(Select(Runner)).all()

        registered = api.get_registered_names()
        for runner in runners:
            if runner.name in registered:
                registered.remove(runner.name)

        self.name_completer.setModel(QStringListModel(registered))

        sess.close()

    def _new_runner(self):
        if not self.runners_list.count() == 0:
            self._save_runner()
        try:
            self._select("")
        except:
            sess = Session(self.mw.db)
            runner = Runner(
                name=f"",
                club="",
                si=0,
                reg=f"",
                call="",
                category=sess.scalars(Select(Category)).first(),
                startlist_time=None,
            )
            sess.add(runner)

            sess.commit()
            sess.close()

            self._select("")

            self._update_runners_cats()

    def _delete_runner(self):
        sess = Session(self.mw.db)
        sess.execute(Delete(Runner).where(Runner.id == self.selected))
        sess.commit()

        self._update_runners_cats()
        if self.runners_list.item(0):
            self._select(self.runners_list.item(0).text())
        else:
            self._new_runner()
        sess.close()

    def _print_readout(self):
        sess = Session(self.mw.db)
        runner = sess.scalars(
            Select(Runner).where(Runner.id == self.selected)
        ).one_or_none()

        if runner:
            inpd = QInputDialog()
            inpd.setComboBoxItems([p.device for p in comports()[::-1]])
            inpd.setLabelText("Vyberte port tiskárny")
            inpd.setWindowTitle("Tisk")
            if inpd.exec() == QInputDialog.DialogCode.Accepted:
                printer = Serial(inpd.textValue())
                print_readout(self.mw.db, runner.si, printer)
                printer.close()

        sess.close()

    def _show(self):
        self._update_runners_cats()
        try:
            self._select(self.runners_list.item(0).text())
        except:
            ...

    def closeEvent(self, event):
        self._save_runner()
        super().closeEvent(event)
