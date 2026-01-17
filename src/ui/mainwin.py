import qtawesome as qta
import sqlalchemy
from PySide6.QtCore import QCoreApplication, QSize
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QMainWindow,
    QHBoxLayout,
    QStackedWidget,
    QWidget,
    QToolButton,
    QVBoxLayout,
    QButtonGroup,
)

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


class IconSidebar(QWidget):
    def __init__(self, parent=None, icon_size=QSize(30, 30), width=56):
        super().__init__(parent)
        self._icon_size = icon_size
        self.setFixedWidth(width)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(6, 6, 6, 6)
        self._layout.setSpacing(6)
        self._layout.addStretch(1)
        self._buttons = []
        self._group = QButtonGroup(self)
        self._group.setExclusive(True)

        self._tooltip = None
        self._top_tooltip = None

        self._hover_label = None

    def add_button(self, icon: QIcon, text: str, idx: int = None):
        btn = QToolButton(self)
        btn.setIcon(icon)
        btn.setToolTip(text)
        btn.setCheckable(True)
        btn.setAutoRaise(True)
        btn.setIconSize(self._icon_size)

        if idx is None:
            idx = len(self._buttons)

        self._layout.insertWidget(self._layout.count() - 1, btn)
        self._buttons.append(btn)

        self._group.addButton(btn, idx)
        return btn

    def connect_clicked(self, callback):
        self._group.buttonClicked.connect(callback)

    def set_current(self, idx: int):
        try:
            btn = self._group.button(idx)
            if btn:
                btn.setChecked(True)
        except Exception:
            pass


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

        self.container = QWidget()
        self.setCentralWidget(self.container)

        layout = QHBoxLayout(self.container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.sidebar = IconSidebar(self)
        layout.addWidget(self.sidebar)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        layout.setStretch(0, 0)
        layout.setStretch(1, 1)

        self._add_page(self.basicinfo_win, QCoreApplication.translate("MainWindow", "Základní info"),
                       qta.icon("mdi6.information-outline"))
        self._add_page(self.controls_win, QCoreApplication.translate("MainWindow", "Kontroly"),
                       qta.icon("mdi6.antenna"))
        self._add_page(self.categories_win, QCoreApplication.translate("MainWindow", "Kategorie"),
                       qta.icon("mdi6.account-group-outline"))
        self._add_page(self.import_win, QCoreApplication.translate("MainWindow", "Import"), qta.icon("mdi6.import"))
        self._add_page(self.runners_win, QCoreApplication.translate("MainWindow", "Běžci"), qta.icon("mdi6.run"))
        self._add_page(self.readout_win, QCoreApplication.translate("MainWindow", "Vyčítání"),
                       qta.icon("mdi6.cable-data"))
        self._add_page(self.startlist_win, QCoreApplication.translate("MainWindow", "Startovka"),
                       qta.icon("mdi6.timer-outline"))
        self._add_page(self.results_win, QCoreApplication.translate("MainWindow", "Výsledky"),
                       qta.icon("mdi6.trophy-outline"))
        self._add_page(self.inforest_win, QCoreApplication.translate("MainWindow", "Závodníci v lese"),
                       qta.icon("mdi6.pine-tree-variant-outline"))
        self._add_page(self.experimental_win, QCoreApplication.translate("MainWindow", "Experimentální"),
                       qta.icon("mdi6.flask"))

        self.stack.setCurrentIndex(0)
        self.sidebar.set_current(0)

    def _add_page(self, widget, label, icon_path=None):
        self.windows.append(widget)
        self.stack.addWidget(widget)

        icon = QIcon(icon_path) if icon_path else QIcon()
        try:
            idx = self.stack.indexOf(widget)
        except Exception:
            idx = -1

        if idx >= 0:
            btn = self.sidebar.add_button(icon, label, idx)
            try:
                btn.clicked.connect(lambda checked=False, i=idx: self._on_sidebar_button_clicked(i))
            except Exception:
                pass

    def _adjust_sidebar_width(self):
        try:
            win_w = max(0, self.width())
        except Exception:
            win_w = 800
        remaining = max(300, win_w - 80)
        try:
            self.stack.setMinimumWidth(remaining)
        except Exception:
            pass

    def show(self, dbstr=None):
        try:
            self.db = sqlalchemy.create_engine(dbstr, max_overflow=-1)
        except Exception:
            self.db = sqlalchemy.create_engine(dbstr)

        super().show()

        try:
            self._adjust_sidebar_width()
        except Exception:
            pass

        if self.stack.count():
            current = self.stack.widget(0)
            if hasattr(current, "_show"):
                current._show()

        models.Base.metadata.create_all(self.db)

        try:
            name = api.get_basic_info(self.db)["name"]
        except Exception:
            name = ""
        self.setWindowTitle(f"JJ ARDFEvent - {name}")

        try:
            self.showMaximized()
        except Exception:
            pass

    def resizeEvent(self, event):
        try:
            self._adjust_sidebar_width()
        except Exception:
            pass
        return super().resizeEvent(event)

    def closeEvent(self, event):
        super().closeEvent(event)
        for win in self.windows:
            win.close()

    def _on_sidebar_button_clicked(self, idx):
        if idx < 0 or idx >= self.stack.count():
            return
        self.stack.setCurrentIndex(idx)
        self.sidebar.set_current(idx)
        w = self.stack.currentWidget()
        if w and hasattr(w, "_show"):
            w._show()
