import csv
from datetime import timedelta
from pathlib import Path

import sqlalchemy
from PySide6.QtWidgets import QWidget, QLineEdit, QFormLayout, QRadioButton, QPushButton, QMessageBox, QFileDialog
from sqlalchemy import Select
from sqlalchemy.orm import Session

import results
from models import Category


class StagesHelperWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Etapový závod")

        lay = QFormLayout()
        self.setLayout(lay)

        self.stages_edit = QLineEdit()
        lay.addRow("ID závodů oddělené středníkem", self.stages_edit)

        self.timetx_radio = QRadioButton("Součet kontrol, příp. časů")
        lay.addRow(self.timetx_radio)

        self.basic_radio = QRadioButton("Prostý součet umístění")
        lay.addRow(self.basic_radio)

        start_btn = QPushButton("Vybrat výstup a spočítat")
        start_btn.clicked.connect(self.calculate)
        lay.addRow(start_btn)

    def calculate(self):
        fn = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            filter="CSV (*.csv)",
        )[0]

        if fn:
            if not fn.endswith(".csv"):
                fn += ".csv"
        else:
            return

        self.close()

        races = self.stages_edit.text().split(";")

        headers = []

        runners = {}
        default = [None for _ in races]

        for e, race in enumerate(races):
            headers.append(f"E{e + 1}")
            try:
                file = (Path.home() / ".ardfevent" / f"{race}.sqlite")
                db = sqlalchemy.create_engine(f"sqlite:///{file}", max_overflow=-1)
                sess = Session(db)
                categories = sess.scalars(Select(Category)).all()

                for category in categories:
                    res = results.calculate_category(db, category.name)
                    for result in res:
                        key = (result.reg or result.name)
                        if key not in runners.keys():
                            runners[key] = default.copy()
                        runners[key][e] = (category.name, result.place, result.time, result.tx,
                                           result.status, result.name)
                sess.close()

            except:
                QMessageBox.warning(self, "Chyba",
                                    f"Nepodařilo se načíst a zpracovat závod {race}. Nebude v etapových výsledkách")

        dsq_without_ok_result = []
        dsq_multiple_categories = []

        cats = {}
        for runner in runners.keys():
            if None in runners[runner] or 0 in map(lambda x: x[1], runners[runner]):
                name = None
                for res in runners[runner]:
                    if res:
                        name = res[5]
                        break
                if name:
                    dsq_without_ok_result.append(name)
                continue

            person_cats = list(set(map(lambda x: x[0], runners[runner])))

            if len(person_cats) != 1:
                dsq_multiple_categories.append(runners[runner][0][5])
                continue

            cat = person_cats[0]
            if cat not in cats.keys():
                cats[cat] = [runners[runner]]
            else:
                cats[cat].append(runners[runner])

        cats_results = {}
        for cat in cats.keys():
            res = []
            for runner in cats[cat]:
                res.append((runner[0][5], sum(map(lambda x: x[1], runner)),
                            (-sum(map(lambda x: x[3], runner)), sum(map(lambda x: x[2], runner)), runner[0][5]),
                            runner))
            cats_results[cat] = sorted(res, key=lambda x: x[1] if self.basic_radio.isChecked() else x[2])

        with open(fn, "w") as f:
            csvw = csv.writer(f, delimiter=";")
            csvw.writerows(
                [["Děkuji, že k datům uvádíte atribuci:",
                  '"Data pocházejí ze StageHelper pro ARDFEvent, (C) Jakub Jiroutek"'],
                 []])

            if dsq_without_ok_result:
                csvw.writerows(
                    [["Nezařazeni kvůli nedostatku OK výsledků:"]] + list(
                        map(lambda x: [x], dsq_without_ok_result)) + [[]])

            if dsq_multiple_categories:
                csvw.writerows(
                    [["Nezařazeni kvůli účasti ve více kategoriích:"]] + list(
                        map(lambda x: [x], dsq_multiple_categories)) + [[]])

            csvw.writerows([["Metoda vyhodnocení:",
                             "Prostý součet umístění" if self.basic_radio.isChecked() else "Součet kontrol a časů"],
                            ["Pro zařazení do celkových výsledků musí být závodník hodnocen ve všech etapách v jedné kategorii."],
                            []])

            for cat_res in cats_results.keys():
                csvw.writerow([cat_res, "", "Σ Čas", "Σ TX", "Σ Umístění"] + headers)
                last_res = None
                last_place = 0
                for i, res in enumerate(cats_results[cat_res]):
                    if res[:2] != last_res:
                        last_place = i + 1
                        last_res = res[:2]
                    individual_res = []
                    for result in res[3]:
                        individual_res.append(
                            f"{results.format_delta(timedelta(seconds=result[2]))}, {result[3]} TX ({result[1]})")
                    csvw.writerow([f"{last_place}.", res[0], results.format_delta(timedelta(seconds=res[2][1])),
                                   f"{-res[2][0]} TX", res[1]] + individual_res)
                csvw.writerow([])
