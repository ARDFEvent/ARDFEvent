from datetime import datetime

from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import Select
from sqlalchemy.orm import Session

from models import Punch, Runner
from results import format_delta


class RunnersInForestWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        lay = QVBoxLayout()
        self.setLayout(lay)

        btn_lay = QHBoxLayout()
        lay.addLayout(btn_lay)

        ochecklist_btn = QPushButton("OCheckList")
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
            .order_by(Runner.reg)
            .order_by(Runner.name)
        ).all()

        self.gen_label.setText(
            f"Generováno v {now.strftime("%H:%M:%S")}, {len(in_forest)} osob v lese"
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

        self.runners_table.horizontalHeader().hide()
        self.runners_table.verticalHeader().hide()

        sess.close()
