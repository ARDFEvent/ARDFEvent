import csv

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import (
    QFileDialog,
    QLabel,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

import api
import import_runners


class ImportWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        lay = QVBoxLayout()
        self.setLayout(lay)

        file_btn = QPushButton(QCoreApplication.translate("ImportWindow", "Vyberte soubor (.csv)"))
        file_btn.clicked.connect(self._select_file)
        lay.addWidget(file_btn)

        lay.addWidget(
            QLabel(
                QCoreApplication.translate("ImportWindow",
                                           'Soubor musí obsahovat hlavičku "Jméno;Příjmení;Registrace;SI;Kategorie", podle toho se musí řídit další sloupce.')
            )
        )
        lay.addWidget(QLabel(QCoreApplication.translate("ImportWindow", "Pro import z ROBis využijte okno ROBis!")))

        self.log = QTextBrowser()
        lay.addWidget(self.log)

    def _select_file(self):
        file = QFileDialog.getOpenFileName(self, "Import CSV", filter="CSV (*.csv)")

        if not file[0]:
            return

        with open(file[0], "r") as f:
            reader = csv.reader(f, delimiter=";")
            data = list(reader)[1:]
            self.log.append(
                QCoreApplication.translate("ImportWindow", "Načten soubor %s. Počet závodníků: %d.") % (file[0],
                                                                                                        len(data)))

        clubs = api.get_clubs()

        runners = []

        for runner in data:
            runners.append(
                import_runners.RunnerToImport(
                    name=f"{runner[1]}, {runner[0]}",
                    reg=runner[2],
                    si=int(runner[3]),
                    category_name=runner[4],
                    call="",
                )
            )

        for code, runner in import_runners.import_runners(self.mw.db, runners, clubs):
            match code:
                case 0:
                    self.log.append(
                        QCoreApplication.translate("ImportWindow",
                                                   "OK: Závodník %s byl úspěšně importován.") % runner.name
                    )
                case 1:
                    self.log.append(
                        QCoreApplication.translate("ImportWindow",
                                                   "/!\\ WAR: Závodník %s s registračním číslem %s již existuje! Přepisuje se.") % (
                            runner.name, runner.reg)
                    )
                case 2:
                    self.log.append(
                        QCoreApplication.translate("ImportWindow",
                                                   "/!\\ WAR: Pro závodníka %s nebyla nalezena kategorie %s! Kategorie vytvořena.") % (
                            runner.name, runner.category_name)
                    )
                case 3:
                    self.log.append(
                        QCoreApplication.translate("ImportWindow",
                                                   "/!\\ WAR: Závodník %s nemá platný klub %s. Přesto se importuje.") % (
                            runner.name, runner.reg[:3])
                    )

    def _show(self):
        self.log.setPlainText("")
