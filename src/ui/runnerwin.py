from datetime import timedelta, datetime

from PySide6.QtCore import QStringListModel, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QCompleter,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget, QInputDialog, QLabel,
)
from sqlalchemy import Delete, Select
from sqlalchemy.orm import Session

import api
from models import Category, Runner


class RunnerWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

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

        self.category_edit = QComboBox()
        details_lay.addRow("Kategorie", self.category_edit)

        self.startno_edit = QSpinBox()
        details_lay.addRow("Startovní číslo", self.startno_edit)

        self.starttime_lbl = QLabel()
        details_lay.addRow("Startovní čas", self.starttime_lbl)

        self.dns_edit = QCheckBox()
        details_lay.addRow("DNS", self.dns_edit)

        self.dsq_edit = QCheckBox()
        details_lay.addRow("DSQ", self.dsq_edit)

        save_btn = QPushButton("Uložit")
        save_btn.clicked.connect(self._save_runner)
        details_lay.addWidget(save_btn)

        print_btn = QPushButton("Vytisknout výčet")
        print_btn.clicked.connect(self._btn_print_readout)
        details_lay.addWidget(print_btn)

        snura_btn = QPushButton("Vytisknout výčet na šňůru")
        snura_btn.clicked.connect(self._btn_print_snura)
        details_lay.addWidget(snura_btn)

        send_btn = QPushButton("Odeslat online")
        send_btn.clicked.connect(self._send_online)
        details_lay.addWidget(send_btn)

        st_btn = QPushButton("Změnit startovní čas")
        st_btn.clicked.connect(self._set_starttime)
        details_lay.addWidget(st_btn)

        delete_btn = QPushButton("Smazat")
        delete_btn.clicked.connect(self._delete_runner)
        details_lay.addWidget(delete_btn)

        self.selected = 0
        self.category_indexes = {}

    def _set_starttime(self):
        with Session(self.mw.db) as sess:
            runner = self._get_runner(sess)
            if runner:
                runner.startlist_time = datetime.fromisoformat(
                    api.get_basic_info(self.mw.db)["date_tzero"]) + timedelta(minutes=
                                                                              QInputDialog.getDouble(
                                                                                  self,
                                                                                  "Startovní čas",
                                                                                  "Zadejte relativní startovní čas (min)",
                                                                                  minValue=-1440,
                                                                                  maxValue=1440,
                                                                                  step=0.1)[0])

            sess.commit()

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
        with Session(self.mw.db) as sess:
            runner = self._get_runner(sess)
            if runner:
                runner.name = self.name_edit.text()
                runner.club = self.club_edit.text()
                runner.si = self.SI_edit.text()
                runner.reg = self.reg_edit.text()
                runner.startno = self.startno_edit.value() or None

                runner.category = sess.scalars(
                    Select(Category).where(
                        Category.name == self.category_edit.currentText()
                    )
                ).one()
                runner.manual_dns = self.dns_edit.isChecked()
                runner.manual_disk = self.dsq_edit.isChecked()

            sess.commit()

        self._update_runners_cats()

    def _select_by_user(self, item: QListWidgetItem):
        text = item.text()
        self._save_runner()
        self._update_runners_cats()
        self._select(text)

    def _send_online(self):
        self.mw.pl.readout(int(self.SI_edit.text()))

    def _select(self, text):
        with Session(self.mw.db) as sess:
            runner = sess.scalars(Select(Runner).where(Runner.name == text)).one_or_none()

            if runner:
                self.name_edit.setText(runner.name)
                self.club_edit.setText(runner.club)
                self.SI_edit.setValue(runner.si)
                self.reg_edit.setText(runner.reg)
                self.startno_edit.setValue(runner.startno or 0)
                self.starttime_lbl.setText(runner.startlist_time.strftime("%H:%M:%S") if runner.startlist_time else "-")

                self.category_edit.setCurrentIndex(
                    self.category_indexes[runner.category.name]
                )

                self.dns_edit.setChecked(runner.manual_dns)
                self.dsq_edit.setChecked(runner.manual_disk)

                self.selected = runner.id
            else:
                raise ValueError("Runner not found")

    def _update_runners_cats(self):
        self.runners_list.clear()

        cat_index = self.category_edit.currentIndex()
        self.category_edit.clear()

        with Session(self.mw.db) as sess:
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

    def _new_runner(self):
        if not self.runners_list.count() == 0:
            self._save_runner()
        try:
            self._select("")
        except:
            with Session(self.mw.db) as sess:
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

            self._select("")

            self._update_runners_cats()

    def _delete_runner(self):
        with Session(self.mw.db) as sess:
            sess.execute(Delete(Runner).where(Runner.id == self.selected))
            sess.commit()

        self._update_runners_cats()
        if self.runners_list.item(0):
            self._select(self.runners_list.item(0).text())
        else:
            self._new_runner()

    def _print_readout(self, snura):
        if self.mw.readout_win.printer:
            with Session(self.mw.db) as sess:
                runner = sess.scalars(
                    Select(Runner).where(Runner.id == self.selected)
                ).one_or_none()

                if runner:
                    self.mw.readout_win.print_readout(runner.si, snura)

    def _btn_print_readout(self):
        self._print_readout(False)

    def _btn_print_snura(self):
        self._print_readout(True)

    def _show(self):
        self._update_runners_cats()
        try:
            self._select(self.runners_list.item(0).text())
        except:
            ...

    def closeEvent(self, event):
        self._save_runner()
        super().closeEvent(event)
