from datetime import datetime
from pathlib import Path

import sqlalchemy
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget, QMenu,
)

import api
import models
from helpers.stages import StagesHelperWindow


class WelcomeWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        self.setWindowTitle("JJ ARDFEvent")

        lay = QVBoxLayout()
        self.setLayout(lay)

        logolay = QHBoxLayout()
        logolay.addStretch()

        img_lbl = QLabel()
        img_lbl.setPixmap(
            QPixmap(":/icons/icon.png").scaled(QSize(300, 300), Qt.AspectRatioMode.KeepAspectRatioByExpanding))
        logolay.addWidget(img_lbl)

        logolay.addStretch()

        lay.addLayout(logolay)

        new_btn = QPushButton("Nový závod")
        new_btn.clicked.connect(self._new_race)
        lay.addWidget(new_btn)

        del_btn = QPushButton("Smazat závod")
        del_btn.clicked.connect(self._delete)
        lay.addWidget(del_btn)

        dbstr_btn = QPushButton("Vlastní DB string")
        dbstr_btn.clicked.connect(self._custom_dbstr)
        lay.addWidget(dbstr_btn)

        self.stage_helper = StagesHelperWindow()

        helpers_menu = QMenu(self)
        helpers_menu.addAction("Etapový závod", self.stage_helper.show)

        helpers_btn = QPushButton("Nástroje")
        helpers_btn.setMenu(helpers_menu)
        lay.addWidget(helpers_btn)

        self.races_list = QListWidget()
        self.races_list.itemDoubleClicked.connect(self._open_race)
        lay.addWidget(self.races_list)

        self._load_races()

    def _custom_dbstr(self):
        dbstr, ok = QInputDialog.getText(self, "Vlastní DB string", "Zadejte DB string")
        if ok:
            self.mw.show(dbstr)
            self.close()

    def _load_races(self):
        self.races_list.clear()

        self.races = []

        for file in (Path.home() / ".ardfevent").glob("*.sqlite"):
            try:
                self.db = sqlalchemy.create_engine(f"sqlite:///{file}", max_overflow=-1)

                title = f"{datetime.fromisoformat(api.get_basic_info(self.db)["date_tzero"]).strftime('%d.%m.%Y %H:%M')} - {api.get_basic_info(self.db)["name"]} ({file.name})"
                self.races.append((title, file))

                self.races_list.addItem(QListWidgetItem(title))
            except:
                ...
        self.setMinimumSize(self.races_list.sizeHintForColumn(0) + 50, 300)

    def _new_race(self):
        title, ok = QInputDialog.getText(self, "Nový závod", "Zadejte ID závodu")
        if ok and title:
            file = Path.home() / ".ardfevent" / f"{title}.sqlite"
            if not file.exists():
                open(file, "w+").close()

            self.db = sqlalchemy.create_engine(f"sqlite:///{file}/", max_overflow=-1)
            models.Base.metadata.create_all(self.db)
            api.set_basic_info(
                self.db,
                {
                    "name": title,
                    "date_tzero": datetime.now().isoformat(),
                    "band": "2m",
                    "limit": 0,
                },
            )

            self.mw.show(f"sqlite:///{file.absolute()}/")
            self.close()
        else:
            return

    def _delete(self):
        item = self.races_list.currentItem()
        if not item:
            return
        if (
                QMessageBox.critical(
                    self,
                    "Smazat závod",
                    f"Opravdu chcete smazat závod {item.text()}?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                == QMessageBox.Yes
        ):
            for title, file in self.races:
                if item.text() == title:
                    file.unlink()
                    self._load_races()
                    break

    def _open_race(self, item: QListWidgetItem):
        for title, file in self.races:
            if item.text() == title:
                self.mw.show(f"sqlite:///{file.absolute()}/")
                self.close()
                break
