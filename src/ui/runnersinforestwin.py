from datetime import datetime, timedelta

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import Select
from sqlalchemy.orm import Session

import api
from models import Punch, Runner
from results import format_delta
from ui.qtaiconbutton import QTAIconButton


class RunnersInForestWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        lay = QVBoxLayout()
        self.setLayout(lay)

        btn_lay = QHBoxLayout()
        lay.addLayout(btn_lay)

        ochecklist_btn = QTAIconButton("mdi6.check-circle", "OCheckList", color="green")
        ochecklist_btn.clicked.connect(self.mw.ochecklist_win.show)
        btn_lay.addWidget(ochecklist_btn)

        btn_lay.addStretch()

        self.gen_label = QLabel("")
        lay.addWidget(self.gen_label)

        self.runners_table = QTableWidget()
        self.runners_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.runners_table)

    def _update(self):
        if self.isVisible():
            self._show()

    def _show(self):
        sess = Session(self.mw.db)
        now = datetime.now()
        in_forest = sess.scalars(
            Select(Runner)
            .where(~Runner.manual_dns)
            .where(~Runner.manual_disk)
            .where(Runner.si.not_in(Select(Punch.si)))
            .where(Runner.startlist_time < now)
            .order_by(Runner.startlist_time)
            .order_by(Runner.name)
        ).all()

        finished = sess.scalars(
            Select(Runner)
            .where(~Runner.manual_dns)
            .where(~Runner.manual_disk)
            .where(Runner.si.in_(Select(Punch.si)))
        ).all()

        not_started_yet = sess.scalars(
            Select(Runner)
            .where(~Runner.manual_dns)
            .where(~Runner.manual_disk)
            .where(Runner.startlist_time > now)
        ).all()

        self.gen_label.setText(
            QCoreApplication.translate("RunnersInForestWindow", "Generováno v %s, ") % now.strftime("%H:%M:%S")
            + (
                QCoreApplication.translate("RunnersInForestWindow",
                                           "VŠICHNI V CÍLI!") if not in_forest else QCoreApplication.translate(
                    "RunnersInForestWindow", "%d osob v lese, %d dokončilo, "
                                             "%d ještě nestartovalo, "
                                             "limit posledního v lese: %s") % (len(finished), len(in_forest),
                                                                               len(not_started_yet), (
                                                                                       in_forest[
                                                                                           -1].startlist_time + timedelta(
                                                                                   minutes=int(
                                                                                       api.get_basic_info(
                                                                                           self.mw.db)[
                                                                                           "limit"]))).strftime(
                        "%H:%M:%S"))
            )
        )

        self.runners_table.clear()
        self.runners_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.runners_table.setColumnCount(4)
        self.runners_table.setRowCount(len(in_forest))

        for i, runner in enumerate(in_forest):
            self.runners_table.setItem(i, 0, QTableWidgetItem(runner.name))
            self.runners_table.setItem(i, 1, QTableWidgetItem(runner.reg))
            self.runners_table.setItem(i, 2, QTableWidgetItem(runner.category.name))

            if runner.startlist_time:
                self.runners_table.setItem(
                    i, 3, QTableWidgetItem(format_delta(now - runner.startlist_time))
                )
            else:
                self.runners_table.setItem(i, 3, QTableWidgetItem("-"))

        self.runners_table.setSortingEnabled(True)
        self.runners_table.verticalHeader().hide()
        self.runners_table.setHorizontalHeaderLabels(
            [QCoreApplication.translate("RunnersInForestWindow", "Jméno"),
             QCoreApplication.translate("RunnersInForestWindow", "Index"),
             QCoreApplication.translate("RunnersInForestWindow", "Kategorie"),
             QCoreApplication.translate("RunnersInForestWindow", "Čas v lese")]
        )

        sess.close()
