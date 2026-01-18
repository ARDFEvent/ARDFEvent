import random
import time
from datetime import timedelta

from dateutil.parser import parser
from PySide6.QtWidgets import (
    QDateTimeEdit,
    QDoubleSpinBox,
    QFormLayout,
    QPushButton,
    QWidget,
)
from sqlalchemy import Select
from sqlalchemy.orm import Session

import api
from models import Category, Runner


class StartlistDrawWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        self.mainlay = QFormLayout()
        self.setLayout(self.mainlay)
        self.setWindowTitle("Startovní listina")

        self.base_interval_edit = QDoubleSpinBox()
        self.base_interval_edit.setSingleStep(0.5)
        self.mainlay.addRow("Startovní interval", self.base_interval_edit)

        self.draw_btn = QPushButton("Losovat!")
        self.draw_btn.clicked.connect(self._draw)
        self.mainlay.addRow(self.draw_btn)

        self.edits = {}

    def show(self):
        self._show()
        super().show()

    def _show(self):
        for edit in self.edits.values():
            self.mainlay.removeRow(edit)

        sess = Session(self.mw.db)

        zero = parser().parse(api.get_basic_info(self.mw.db)["date_tzero"])

        categories = sess.scalars(Select(Category)).all()

        for cat in categories:
            if not len(
                sess.scalars(Select(Runner).where(Runner.category == cat)).all()
            ):
                continue

            cat_edit = QDateTimeEdit()
            cat_edit.setDateTime(zero)

            self.mainlay.addRow(cat.name, cat_edit)
            self.edits[cat.name] = cat_edit

        sess.close()

    def _draw(self):
        baseint_delta = timedelta(seconds=self.base_interval_edit.value() * 60)
        sess = Session(self.mw.db)
        for cat_name in self.edits.keys():
            cat = sess.scalars(
                Select(Category).where(Category.name == cat_name)
            ).first()
            runners = list(
                sess.scalars(Select(Runner).where(Runner.category == cat)).all()
            )

            clubs_dict = {}

            for runner in runners:
                if runner.club not in clubs_dict:
                    clubs_dict[runner.club] = [runner]
                else:
                    clubs_dict[runner.club].append(runner)

            clubs = list(clubs_dict.values())

            clubs.sort(key=len, reverse=True)

            cat_zero = self.edits[cat_name].dateTime().toPython()

            i = 0
            while len(clubs) != 0:
                for club in clubs:
                    random.shuffle(club)
                    club[0].startlist_time = cat_zero + baseint_delta * i
                    club.pop(0)
                    i += 1
                while [] in clubs:
                    clubs.remove([])

        sess.commit()
        sess.close()

        self.mw.startlist_win._update_startlist()
