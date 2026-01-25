from datetime import datetime
from pathlib import Path

import sqlalchemy
from PySide6.QtCore import QSize, Qt, QCoreApplication
from PySide6.QtGui import QPixmap, QPalette
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QWidget, QMenu, QScrollArea, QApplication, )

import api
import migrations
import models
from ui.pluginmanagerwin import PluginManagerWindow
from ui.qtaiconbutton import QTAIconButton


class RaceLine(QWidget):
    def __init__(self, file: Path, ww):
        super().__init__()

        self.ww = ww
        self.file = file

        migrations.migrate(f"sqlite:///{file}")
        self.db = sqlalchemy.create_engine(f"sqlite:///{file}", max_overflow=-1)

        name = api.get_basic_info(self.db)["name"]
        self.date = datetime.fromisoformat(api.get_basic_info(self.db)["date_tzero"])

        lay = QVBoxLayout()
        self.setLayout(lay)

        det_lay = QHBoxLayout()
        lay.addLayout(det_lay)

        det_lay.addWidget(QLabel(self.date.strftime('%d.%m.%Y %H:%M')))
        det_lay.addStretch()

        fn_lbl = QLabel(file.name)
        fn_font = fn_lbl.font()
        fn_font.setPointSize(fn_font.pointSize() - 2)
        fn_lbl.setFont(fn_font)
        det_lay.addWidget(fn_lbl)

        title_lbl = QLabel(name)
        title_font = fn_lbl.font()
        title_font.setPointSize(title_font.pointSize() + 2)
        title_font.setBold(True)
        title_lbl.setFont(title_font)
        lay.addWidget(title_lbl)

        self.setAutoFillBackground(True)

    def mousePressEvent(self, event, /):
        self.ww.deactivate_races()
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, pal.color(QPalette.ColorRole.Highlight))
        self.setPalette(pal)

    def mouseDoubleClickEvent(self, event, /):
        self.ww.mw.show(f"sqlite:///{self.file.absolute()}")
        self.ww.close()


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

        btn_lay = QHBoxLayout()
        lay.addLayout(btn_lay)

        btn_lay.addStretch()

        new_btn = QTAIconButton("mdi6.calendar-plus", QCoreApplication.translate("WelcomeWindow", "Nový závod"))
        new_btn.clicked.connect(self._new_race)
        btn_lay.addWidget(new_btn)

        del_btn = QTAIconButton("mdi6.calendar-remove", QCoreApplication.translate("WelcomeWindow", "Smazat závod"))
        del_btn.clicked.connect(self._delete)
        btn_lay.addWidget(del_btn)

        self.helpers_menu = QMenu(self)

        self.pluginmanagerwin = PluginManagerWindow(self.mw)

        self.helpers_menu.addAction(
            QCoreApplication.translate("WelcomeWindow", "Správce pluginů"), self.pluginmanagerwin.show)

        helpers_btn = QTAIconButton("mdi6.hammer-wrench", QCoreApplication.translate("WelcomeWindow", "Nástroje"),
                                    extra_width=16)
        helpers_btn.setMenu(self.helpers_menu)
        btn_lay.addWidget(helpers_btn)

        btn_lay.addStretch()

        self.races_scroll = QScrollArea()
        self.races_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.races_list = QWidget()
        self.races_lay = QVBoxLayout()
        self.races_list.setLayout(self.races_lay)
        self._load_races()
        self.races_scroll.setWidget(self.races_list)
        lay.addWidget(self.races_scroll)

    def _load_races(self):
        race_lines = []
        for file in (Path.home() / ".ardfevent").glob("*.sqlite"):
            try:
                race_lines.append(RaceLine(file, self))
            except:
                ...
        for line in sorted(race_lines, key=lambda x: x.date, reverse=True):
            self.races_lay.addWidget(line)
        self.setMinimumWidth(self.races_list.sizeHint().width() + 37)

    def _new_race(self):
        title, ok = QInputDialog.getText(self, QCoreApplication.translate("WelcomeWindow", "Nový závod"),
                                         QCoreApplication.translate("WelcomeWindow", "Zadejte ID závodu"))
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

    def deactivate_races(self):
        for i in range(self.races_lay.count()):
            self.races_lay.itemAt(i).widget().setPalette(QApplication.palette())

    def _delete(self):
        item = self.races_list.currentItem()
        if not item:
            return
        if (
                QMessageBox.critical(
                    self,
                    QCoreApplication.translate("WelcomeWindow", "Smazat závod"),
                    QCoreApplication.translate("WelcomeWindow", "Opravdu chcete smazat závod %s?") % item.text(),
                    QMessageBox.Yes | QMessageBox.No,
                )
                == QMessageBox.Yes
        ):
            for title, file in self.races:
                if item.text() == title:
                    file.unlink()
                    self._load_races()
                    break
