import random
from datetime import timedelta, datetime

from PySide6.QtCore import Qt, QSize, QCoreApplication
from PySide6.QtWidgets import (
    QDoubleSpinBox,
    QFormLayout,
    QPushButton,
    QWidget, QListWidget, QListWidgetItem, QSpinBox, QLabel, QVBoxLayout,
)
from sqlalchemy import Select
from sqlalchemy.orm import Session

import api
from models import Category, Runner

COLORS = [Qt.GlobalColor.red, Qt.GlobalColor.darkGreen, Qt.GlobalColor.darkBlue, Qt.GlobalColor.darkMagenta,
          Qt.GlobalColor.darkYellow, Qt.GlobalColor.darkCyan]


class StartListDrawSetupWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        self.mainlay = QFormLayout()
        self.setLayout(self.mainlay)
        self.setWindowTitle(QCoreApplication.translate("StartListDrawWindow", "Nastavení losování startovní listiny"))

        self.draw_btn = QPushButton(QCoreApplication.translate("StartListDrawWindow", "Otevřít losování"))
        self.draw_btn.clicked.connect(self._open_draw)
        self.mainlay.addRow(self.draw_btn)

        self.mainlay.addRow("", QLabel(QCoreApplication.translate("StartListDrawWindow", "Losovací řádek")))

        self.edits = {}

    def _open_draw(self):
        param = []
        lines = 0
        for cat_name, edit in self.edits.items():
            param.append((cat_name, edit.value()))
            lines = max(lines, edit.value())
        self.mw.startlistdraw_win.show(param, lines)
        self.close()

    def show(self):
        self._show()
        super().show()

    def _show(self):
        for edit in self.edits.values():
            self.mainlay.removeRow(edit)

        with Session(self.mw.db) as sess:
            categories = sess.scalars(Select(Category)).all()

            for cat in categories:
                if not len(
                        sess.scalars(Select(Runner).where(Runner.category == cat)).all()
                ):
                    continue

                cat_edit = QSpinBox()
                cat_edit.setMinimum(1)

                self.mainlay.addRow(cat.name, cat_edit)
                self.edits[cat.name] = cat_edit


class StartlistDrawWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        self.setup_win = StartListDrawSetupWindow(mw)

        self.parlay = QVBoxLayout()
        self.setLayout(self.parlay)

        self.mainlay = QFormLayout()
        self.parlay.addLayout(self.mainlay)
        self.setWindowTitle(QCoreApplication.translate("StartListDrawWindow", "Startovní listina"))

        self.base_interval_edit = QDoubleSpinBox()
        self.base_interval_edit.setSingleStep(0.5)
        self.mainlay.addRow(QCoreApplication.translate("StartListDrawWindow", "Startovní interval"),
                            self.base_interval_edit)

        self.draw_btn = QPushButton(QCoreApplication.translate("StartListDrawWindow", "Losovat!"))
        self.draw_btn.clicked.connect(self._draw)
        self.mainlay.addRow(self.draw_btn)

        self.parlay.addStretch(2)

        self.lines = []

    def show(self, param, lines):
        self._show(param, lines)
        super().showMaximized()

    def _show(self, param, lines):
        for line in self.lines:
            self.mainlay.removeRow(line)

        self.lines = []

        for i in range(lines):
            line = QListWidget()
            self.mainlay.addRow(QCoreApplication.translate("StartListDrawWindow", "Los. řádek %d" % (i + 1)), line)

            line.setFlow(QListWidget.Flow.LeftToRight)

            line.setDragEnabled(True)
            line.setDragDropMode(QListWidget.DragDropMode.InternalMove)
            line.setMaximumHeight(60)

            self.lines.append(line)

        with Session(self.mw.db) as sess:
            i = 0
            for name, line in param:
                runners = len(
                    sess.scalars(Select(Runner).where(Runner.category.has(name=name))).all()
                )
                item = QListWidgetItem(f"{name}\n{runners}")
                item.setSizeHint(QSize(runners * 40, 50))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setBackground(COLORS[i % len(COLORS)])
                self.lines[line - 1].addItem(item)
                i += 1

    def draw_category(self, cat_name, cat_zero, baseint_delta):
        last = cat_zero
        with Session(self.mw.db) as sess:
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

            i = 0
            while len(clubs) != 0:
                for club in clubs:
                    random.shuffle(club)
                    club[0].startlist_time = last
                    last = club[0].startlist_time + baseint_delta
                    club.pop(0)
                    i += 1
                while [] in clubs:
                    clubs.remove([])
            sess.commit()
        return last

    def _draw(self):
        baseint_delta = timedelta(seconds=self.base_interval_edit.value() * 60)
        with Session(self.mw.db) as sess:
            for line in self.lines:
                last = datetime.fromisoformat(api.get_basic_info(self.mw.db)["date_tzero"])
                for item in line.findItems("*", Qt.MatchWildcard):
                    cat_name = item.text().split("\n")[0]
                    last = self.draw_category(cat_name, last, baseint_delta)
        sess.commit()

        self.mw.startlist_win._update_startlist()
