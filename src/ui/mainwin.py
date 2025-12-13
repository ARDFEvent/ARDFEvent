import sqlalchemy
from PySide6.QtCore import QCoreApplication
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
    runnersinforestwin,
    runnerwin,
    startlistdrawwin,
    startlistwin,
    welcomewin,
    experimentalwin,
    startnowin,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.welcomewin = welcomewin.WelcomeWindow(self)

        self.basicinfo_win = basicinfowin.BasicInfoWindow(self)
        self.controls_win = controlswin.ControlsWindow(self)
        self.categories_win = categorieswin.CategoriesWindow(self)
        self.import_win = importwin.ImportWindow(self)
        self.runners_win = runnerwin.RunnerWindow(self)
        self.readout_win = readoutwin.ReadoutWindow(self)
        self.results_win = resultswin.ResultsWindow(self)
        self.startno_win = startnowin.StartNumberWindow(self)
        self.startlistdraw_win = startlistdrawwin.StartlistDrawWindow(self)
        self.startlist_win = startlistwin.StartlistWindow(self)
        self.ochecklist_win = ochecklistwin.OCheckListWindow(self)
        self.inforest_win = runnersinforestwin.RunnersInForestWindow(self)
        self.experimental_win = experimentalwin.ExperimentalWindow(self)

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
            self.startlist_win,
            self.ochecklist_win,
            self.inforest_win,
            self.experimental_win,
        ]

        self.mainwid = QTabWidget()
        self.setCentralWidget(self.mainwid)

        self.mainwid.addTab(self.basicinfo_win, QCoreApplication.translate("MainWindow", "Základní info"))
        self.mainwid.setTabIcon(0, QIcon(":/icons/gear.png"))

        self.mainwid.addTab(self.controls_win, QCoreApplication.translate("MainWindow", "Kontroly"))
        self.mainwid.setTabIcon(1, QIcon(":/icons/tx.png"))

        self.mainwid.addTab(self.categories_win, QCoreApplication.translate("MainWindow", "Kategorie"))
        self.mainwid.setTabIcon(2, QIcon(":/icons/categories.png"))

        self.mainwid.addTab(self.import_win, QCoreApplication.translate("MainWindow", "Import"))
        self.mainwid.setTabIcon(3, QIcon(":/icons/import.png"))

        self.mainwid.addTab(self.runners_win, QCoreApplication.translate("MainWindow", "Běžci"))
        self.mainwid.setTabIcon(4, QIcon(":/icons/runners.png"))

        self.mainwid.addTab(self.readout_win, QCoreApplication.translate("MainWindow", "Vyčítání"))
        self.mainwid.setTabIcon(5, QIcon(":/icons/readout.png"))

        self.mainwid.addTab(self.startlist_win, QCoreApplication.translate("MainWindow", "Startovka"))
        self.mainwid.setTabIcon(6, QIcon(":/icons/startlist.png"))

        self.mainwid.addTab(self.results_win, QCoreApplication.translate("MainWindow", "Výsledky"))
        self.mainwid.setTabIcon(7, QIcon(":/icons/results.png"))

        self.mainwid.addTab(self.inforest_win, QCoreApplication.translate("MainWindow", "Závodníci v lese"))
        self.mainwid.setTabIcon(8, QIcon(":/icons/inforest.png"))

        self.mainwid.addTab(self.experimental_win, QCoreApplication.translate("MainWindow", "Experimentální"))
        self.mainwid.setTabIcon(9, QIcon(":/icons/experimental.png"))

        self.mainwid.setTabPosition(QTabWidget.TabPosition.North)

    def show(self, dbstr):
        try:
            self.db = sqlalchemy.create_engine(dbstr, max_overflow=-1)
        except:
            self.db = sqlalchemy.create_engine(dbstr)

        self.mainwid.currentChanged.connect(self._on_tab_changed)

        super().show()
        self.windows[0]._show()

        models.Base.metadata.create_all(self.db)

        self.setWindowTitle(f"JJ ARDFEvent - {api.get_basic_info(self.db)["name"]}")

        self.showMaximized()

    def _on_tab_changed(self, index):
        self.mainwid.currentWidget()._show()

    def closeEvent(self, event):
        super().closeEvent(event)
        for win in self.windows:
            win.close()
