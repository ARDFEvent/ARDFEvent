import glob
import json
from pathlib import Path

from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QInputDialog, QTableWidget, QTableWidgetItem, \
    QAbstractItemView, QHeaderView, QLabel
from dulwich import porcelain


class PluginManagerWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        self.setWindowTitle("Správce pluginů")

        lay = QVBoxLayout()
        self.setLayout(lay)

        installbtn = QPushButton("Nainstalovat plugin")
        installbtn.clicked.connect(self._install_plugin)
        lay.addWidget(installbtn)

        updatebtn = QPushButton("Aktualizovat všechny pluginy")
        updatebtn.clicked.connect(self._update)
        lay.addWidget(updatebtn)

        lay.addWidget(QLabel(f"Cesta do složky s pluginy: {(Path.home() / ".ardfevent" / "plugins").absolute()}"))

        self.table = QTableWidget()
        lay.addWidget(self.table)

    def show(self):
        super().show()
        plugins = glob.glob(str((Path.home() / ".ardfevent" / "plugins").absolute()) + "/**/plugin.json")
        self.table.clear()
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.table.setRowCount(len(plugins))
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["Název", "Verze", "Popis", "Autor", "Složka"]
        )
        self.table.verticalHeader().hide()
        for i, pluginp in enumerate(plugins):
            with open(pluginp, "r", encoding="utf-8") as pf:
                pl = json.load(pf)
            self.table.setItem(i, 0, QTableWidgetItem(pl["name"]))
            self.table.setItem(i, 1, QTableWidgetItem(pl["version"]))
            self.table.setItem(i, 2, QTableWidgetItem(pl["description"]))
            self.table.setItem(i, 3, QTableWidgetItem(pl["author"]))
            self.table.setItem(i, 4, QTableWidgetItem(Path(pluginp).parent.name + "/"))

    def _update(self):
        plugins = glob.glob(str((Path.home() / ".ardfevent" / "plugins").absolute()) + "/**/plugin.json")
        for pluginp in plugins:
            porcelain.pull(porcelain.Repo(Path(pluginp).parent))

    def _install_plugin(self):
        url, ok = QInputDialog.getText(self, "Instalace pluginu", "Zadejte URL pluginu:")
        if ok:
            porcelain.clone(url, Path.home() / ".ardfevent" / "plugins" / url.split("/")[-1].replace(".git", ""))
            self.mw.pl.load_plugin(
                Path.home() / ".ardfevent" / "plugins" / url.split("/")[-1].replace(".git", "") / "plugin.json")
            self.show()
