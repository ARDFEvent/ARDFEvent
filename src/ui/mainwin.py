import json
from datetime import datetime
from pathlib import Path

import qtawesome as qta
import sqlalchemy
from PySide6.QtCore import QCoreApplication, QSize, Qt
from PySide6.QtGui import QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QHBoxLayout,
    QStackedWidget,
    QWidget,
    QToolButton,
    QVBoxLayout,
    QButtonGroup, QMainWindow, QFileDialog, QPushButton, QSizePolicy,
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
    experimentalwin,
    startnowin, mapwin
)
from ui.pluginmanagerwin import PluginManagerWindow


class IconSidebar(QWidget):
    def __init__(self, parent=None, icon_size=QSize(30, 30), width=180, collapsed_width=56):
        super().__init__(parent)
        self._icon_size = icon_size
        self._full_width = width
        self._collapsed_width = collapsed_width
        self._is_collapsed = False

        self.setFixedWidth(self._full_width)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(6, 6, 6, 6)
        self._layout.setSpacing(6)

        self._toggle_btn = QToolButton(self)
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.setAutoRaise(True)
        try:
            self._toggle_btn.setIcon(qta.icon("mdi6.chevron-left"))
        except Exception:
            self._toggle_btn.setIcon(QIcon())
        self._toggle_btn.setIconSize(QSize(16, 16))
        self._toggle_btn.clicked.connect(self.toggle)
        self._layout.insertWidget(0, self._toggle_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

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
        btn.setText(text)
        btn.setToolTip(text)
        btn.setCheckable(True)
        btn.setAutoRaise(True)
        btn.setIconSize(self._icon_size)
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        if self._is_collapsed:
            btn.setToolButtonStyle(Qt.ToolButtonStyle(0))  # QToolButton.ToolButtonIconOnly
        else:
            btn.setToolButtonStyle(Qt.ToolButtonStyle(2))  # QToolButton.ToolButtonTextBesideIcon

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

    def toggle(self):
        self.set_collapsed(not self._is_collapsed)

    def set_collapsed(self, collapsed: bool):
        self._is_collapsed = bool(collapsed)
        if self._is_collapsed:
            self.setFixedWidth(self._collapsed_width)
            for b in self._buttons:
                b.setIconSize(self._icon_size)
                b.setToolButtonStyle(Qt.ToolButtonStyle(0))  # QToolButton.ToolButtonIconOnly
            try:
                self._toggle_btn.setIcon(qta.icon("mdi6.chevron-right"))
            except Exception:
                self._toggle_btn.setIcon(QIcon())
            self._toggle_btn.setChecked(True)
        else:
            self.setFixedWidth(self._full_width)
            for b in self._buttons:
                b.setIconSize(self._icon_size)
                b.setToolButtonStyle(Qt.ToolButtonStyle(2))  # QToolButton.ToolButtonTextBesideIcon
            try:
                self._toggle_btn.setIcon(qta.icon("mdi6.chevron-left"))
            except Exception:
                self._toggle_btn.setIcon(QIcon())
            self._toggle_btn.setChecked(False)

        parent = self.parent()
        if parent and hasattr(parent, "_adjust_sidebar_width"):
            try:
                parent._adjust_sidebar_width()
            except Exception:
                pass


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("JJ ARDFEvent")

        self.racewin = None

        self.plug_pages = []

        self.file_menu = self.menuBar().addMenu("&Soubor")
        self.file_menu.addAction(qta.icon("mdi6.calendar-plus"), QCoreApplication.translate("MainWindow", "Nový"),
                                 QKeySequence.StandardKey.New,
                                 self._new)
        self.file_menu.addAction(qta.icon("mdi6.folder-open-outline"),
                                 QCoreApplication.translate("MainWindow", "Otevřít"), QKeySequence.StandardKey.Open,
                                 self._open)

        self.last_menu = self.file_menu.addMenu(qta.icon("mdi6.calendar-clock"), "&Poslední")

        self.pluginmanagerwin = PluginManagerWindow(self)
        self.plug_menu = self.menuBar().addMenu("Plu&giny")
        self.plug_menu.addAction(
            QCoreApplication.translate("MainWindow", "Správce pluginů"), self.pluginmanagerwin.show)

        self._placeholder = QWidget(self)
        ph_layout = QVBoxLayout(self._placeholder)
        ph_layout.setContentsMargins(0, 0, 0, 0)
        ph_layout.setSpacing(0)
        ph_btn = QPushButton(QCoreApplication.translate("MainWindow", "Otevřete závod..."), self._placeholder)
        ph_btn.clicked.connect(self._open)
        ph_btn.setStyleSheet("font-size: 32pt; font-weight: bold; padding: 32px;")
        ph_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        ph_layout.addStretch(1)
        ph_layout.addWidget(ph_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        ph_layout.addStretch(1)
        self.setCentralWidget(self._placeholder)

        self._update_last_menu()

        self.showMaximized()

    def _update_last_menu(self):
        self.last_menu.clear()
        last = json.loads(api.get_config_value("last_opened", "[]"))
        for i, file in enumerate(last):
            action = self.last_menu.addAction(f"{i + 1}: {file}")
            action.triggered.connect(lambda checked=False, f=file: self._open(dbstr=f))

    def _new(self):
        if dbfile := \
                QFileDialog.getSaveFileName(self, QCoreApplication.translate("MainWindow", "Nový závod"), "",
                                            "ARDFEvent databáze (*.ardf);;Všechny soubory (*)")[0]:
            if not dbfile.endswith(".ardf"):
                dbfile += ".ardf"

            if not Path(dbfile).exists():
                open(dbfile, "w+").close()

            dbstr = f"sqlite:///{dbfile}"

            self.db = sqlalchemy.create_engine(dbstr, max_overflow=-1)
            models.Base.metadata.create_all(self.db)
            api.set_basic_info(
                self.db,
                {
                    "name": Path(dbfile).name,
                    "date_tzero": datetime.now().isoformat(),
                    "band": "80m",
                    "organizer": "",
                    "limit": 0,
                },
            )

            self._open(dbstr=dbstr, last=True)

    def _open(self, *args, dbstr=None, last=False):
        if not dbstr:
            if dbfile := \
                    QFileDialog.getOpenFileName(self, QCoreApplication.translate("MainWindow", "Otevřít závod"), "",
                                                "ARDFEvent databáze (*.ardf);;ARDFEvent databáze - pre 1.1 (*.sqlite);;Všechny soubory (*)")[
                        0]:
                dbstr = f"sqlite:///{dbfile}"
                self._push_last(dbstr)
            else:
                return
        elif last:
            self._push_last(dbstr)

        if self.racewin:
            self.racewin.deleteLater()
            self.racewin = None

        self.racewin = RaceWindow(dbstr)

        for page in self.plug_pages:
            self.racewin.add_page(page[0], page[1], page[2])

        self.setCentralWidget(self.racewin)

        self.db = self.racewin.db

        self.racewin._show()

    def _push_last(self, file):
        last = json.loads(api.get_config_value("last_opened", "[]"))
        if not file in last:
            last.insert(0, file)
            api.set_config_value("last_opened", json.dumps(last[:10]))
        self._update_last_menu()

    def _add_page(self, widget, label, icon_path=None):
        self.plug_pages.append((widget, label, icon_path))

    def show(self, dbstr=None):
        if dbstr:
            self._open(dbstr=dbstr)
        super().showMaximized()


class RaceWindow(QWidget):
    def __init__(self, dbstr=None):
        super().__init__()

        self._shortcuts = []

        try:
            self.db = sqlalchemy.create_engine(dbstr, max_overflow=-1)
        except Exception:
            self.db = sqlalchemy.create_engine(dbstr)

        models.Base.metadata.create_all(self.db)

        api.migrate_basic_info(self.db)

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
        self.map_win = mapwin.MapWindow(self)
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
            self.map_win,
            self.experimental_win,
        ]

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.sidebar = IconSidebar(self)
        layout.addWidget(self.sidebar)
        self.sidebar.set_collapsed(True)
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        layout.setStretch(0, 0)
        layout.setStretch(1, 1)

        self.add_page(self.basicinfo_win, QCoreApplication.translate("MainWindow", "Základní info"),
                      qta.icon("mdi6.information-outline"))
        self.add_page(self.controls_win, QCoreApplication.translate("MainWindow", "Kontroly"),
                      qta.icon("mdi6.antenna"))
        self.add_page(self.categories_win, QCoreApplication.translate("MainWindow", "Kategorie"),
                      qta.icon("mdi6.account-group-outline"))
        # self.add_page(self.import_win, QCoreApplication.translate("MainWindow", "Import"), qta.icon("mdi6.import"))
        self.add_page(self.runners_win, QCoreApplication.translate("MainWindow", "Běžci"), qta.icon("mdi6.run"))
        self.add_page(self.readout_win, QCoreApplication.translate("MainWindow", "Vyčítání"),
                      qta.icon("mdi6.cable-data"))
        self.add_page(self.startlist_win, QCoreApplication.translate("MainWindow", "Startovka"),
                      qta.icon("mdi6.timer-outline"))
        self.add_page(self.results_win, QCoreApplication.translate("MainWindow", "Výsledky"),
                      qta.icon("mdi6.trophy-outline"))
        self.add_page(self.inforest_win, QCoreApplication.translate("MainWindow", "Závodníci v lese"),
                      qta.icon("mdi6.pine-tree-variant-outline"))
        self.add_page(self.map_win, QCoreApplication.translate("MainWindow", "Mapa"),
                      qta.icon("mdi6.map-outline"))
        # self.add_page(self.experimental_win, QCoreApplication.translate("MainWindow", "Experimentální"),
        #               qta.icon("mdi6.flask"))

        self.stack.setCurrentIndex(0)
        self.sidebar.set_current(0)

    def _show(self):
        try:
            self._adjust_sidebar_width()
        except:
            pass

        if self.stack.count():
            current = self.stack.widget(0)
            if hasattr(current, "_show"):
                current._show()

    def add_page(self, widget, label, icon_path=None):
        self.windows.append(widget)
        self.stack.addWidget(widget)

        icon = QIcon(icon_path) if icon_path else QIcon()
        try:
            idx = self.stack.indexOf(widget)
        except:
            idx = -1

        if idx >= 0:
            btn = self.sidebar.add_button(icon, label, idx)
            try:
                btn.clicked.connect(lambda checked=False, i=idx: self._on_sidebar_button_clicked(i))
                try:
                    seq = None
                    if 0 <= idx <= 9:
                        seq = f"Alt+{(idx + 1) % 10}"
                        sc = QShortcut(QKeySequence(seq), self)
                        sc.activated.connect(lambda i=idx: self._on_sidebar_button_clicked(i))
                        self._shortcuts.append(sc)
                    elif 10 <= idx <= 21:
                        fnum = idx - 9
                        seq = f"Shift+Alt+{fnum}"
                        sc = QShortcut(QKeySequence(seq), self)
                        sc.activated.connect(lambda i=idx: self._on_sidebar_button_clicked(i))
                        self._shortcuts.append(sc)
                    if seq:
                        btn.setToolTip(f"{label} ({seq})")
                except Exception:
                    pass
            except:
                pass

    def _adjust_sidebar_width(self):
        try:
            win_w = max(0, self.width())
        except:
            win_w = 800
        try:
            sidebar_w = self.sidebar.width() if hasattr(self, "sidebar") else 80
        except:
            sidebar_w = 80

        remaining = max(300, win_w - sidebar_w - 24)
        try:
            self.stack.setMinimumWidth(remaining)
        except:
            pass

    def resizeEvent(self, event):
        try:
            self._adjust_sidebar_width()
        except:
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
