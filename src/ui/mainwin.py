import sqlalchemy
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMainWindow, QTabWidget

import api
import models
from ui import (
    basicinfowin,
    categorieswin,
    controlswin,
    importwin,
    ochecklistwin,
    readoutwin,
    resultswin,
    robiswin,
    runnersinforestwin,
    runnerwin,
    startlistdrawwin,
    startlistwin,
    welcomewin,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.welcomewin = welcomewin.WelcomeWindow(self)

    def show(self, dbstr):
        super().show()

        self.db = sqlalchemy.create_engine(dbstr, max_overflow=-1)
        models.Base.metadata.create_all(self.db)

        self.setWindowTitle(f"JJ ARDFEvent - {api.get_basic_info(self.db)["name"]}")

        self.basicinfo_win = basicinfowin.BasicInfoWindow(self)
        self.controls_win = controlswin.ControlsWindow(self)
        self.categories_win = categorieswin.CategoriesWindow(self)
        self.import_win = importwin.ImportWindow(self)
        self.runners_win = runnerwin.RunnerWindow(self)
        self.readout_win = readoutwin.ReadoutWindow(self)
        self.results_win = resultswin.ResultsWindow(self)
        self.startlistdraw_win = startlistdrawwin.StartlistDrawWindow(self)
        self.startlist_win = startlistwin.StartlistWindow(self)
        self.ochecklist_win = ochecklistwin.OCheckListWindow(self)
        self.inforest_win = runnersinforestwin.RunnersInForestWindow(self)
        self.robis_win = robiswin.ROBisWindow(self)

        self.windows = [
            self.basicinfo_win,
            self.controls_win,
            self.categories_win,
            self.import_win,
            self.runners_win,
            self.readout_win,
            self.results_win,
            self.startlist_win,
            self.startlistdraw_win,
            self.ochecklist_win,
            self.inforest_win,
            self.robis_win,
        ]

        self.mainwid = QTabWidget()
        self.setCentralWidget(self.mainwid)
        self.mainwid.currentChanged.connect(self._on_tab_changed)

        self.mainwid.addTab(self.basicinfo_win, "Základní info")
        self.mainwid.setTabIcon(0, QIcon(":/icons/gear.png"))

        self.mainwid.addTab(self.controls_win, "Kontroly")
        self.mainwid.setTabIcon(1, QIcon(":/icons/tx.png"))

        self.mainwid.addTab(self.categories_win, "Kategorie")
        self.mainwid.setTabIcon(2, QIcon(":/icons/categories.png"))

        self.mainwid.addTab(self.import_win, "Import")
        self.mainwid.setTabIcon(3, QIcon(":/icons/import.png"))

        self.mainwid.addTab(self.runners_win, "Běžci")
        self.mainwid.setTabIcon(4, QIcon(":/icons/runners.png"))

        self.mainwid.addTab(self.readout_win, "Vyčítání")
        self.mainwid.setTabIcon(5, QIcon(":/icons/readout.png"))

        self.mainwid.addTab(self.startlist_win, "Startovka")
        self.mainwid.setTabIcon(6, QIcon(":/icons/startlist.png"))

        self.mainwid.addTab(self.results_win, "Výsledky")
        self.mainwid.setTabIcon(7, QIcon(":/icons/results.png"))

        self.mainwid.addTab(self.inforest_win, "Závodníci v lese")
        self.mainwid.setTabIcon(8, QIcon(":/icons/inforest.png"))

        self.mainwid.addTab(self.robis_win, "ROBis")
        self.mainwid.setTabIcon(9, QIcon(":/icons/robis.png"))

        self.mainwid.setTabPosition(QTabWidget.TabPosition.North)

        self.showMaximized()

    def _on_tab_changed(self, index):
        self.mainwid.currentWidget()._show()

    def closeEvent(self, event):
        super().closeEvent(event)
        for win in self.windows:
            win.close()
