from datetime import timedelta

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import Select
from sqlalchemy.orm import Session

import exports.csv_results as res_csv
import exports.html_results as res_html
import exports.json_results as res_json
import exports.xml_results as res_xml
import results
from models import Category
from ui.previewwin import PreviewWindow
from web.webserver import ARDFEventServer


class WebServerThread(QThread):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.server = ARDFEventServer(db)

    def set_ann(self, ann):
        self.server.announcement = ann

    def run(self):
        self.server.run_server()

    def terminate(self):
        return super().terminate()


class ResultsWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw
        self.pws = []
        self.proc = None

        lay = QVBoxLayout()
        self.setLayout(lay)

        btn_lay = QHBoxLayout()
        lay.addLayout(btn_lay)

        export_menu = QMenu(self)
        export_menu.addAction("HTML", self._export_html)
        export_menu.addAction("HTML s mezičasy", self._export_html_splits)
        export_menu.addAction("IOF XML 3.0", self._export_iof_xml)
        export_menu.addAction("ARDF JSON", self._export_json)
        export_menu.addAction("CSV", self._export_csv)

        export_btn = QPushButton("Exportovat")
        export_btn.setMenu(export_menu)
        btn_lay.addWidget(export_btn)

        self.webserverbtn = QPushButton("Spustit webový server")
        self.webserverbtn.clicked.connect(self._toggle_webserver)
        btn_lay.addWidget(self.webserverbtn)

        self.state_label = QLabel()
        btn_lay.addWidget(self.state_label)

        self.annbtn = QPushButton("Změna hlášení")
        self.annbtn.clicked.connect(self._set_webserver_announcement)
        btn_lay.addWidget(self.annbtn)

        self._proc_stopped()

        btn_lay.addStretch()

        self.results_table = QTableWidget()
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.results_table)

    def _set_webserver_announcement(self):
        ann, ok = QInputDialog.getText(self, "Změna hlášení", "Zadejte hlášení")

        if self.proc and ok:
            self.proc.set_ann(ann)

    def _toggle_webserver(self):
        if not self.proc:
            self.webserverbtn.setDisabled(True)
            self.proc = WebServerThread(self.mw.db)
            self.proc.started.connect(self._proc_running)
            self.proc.finished.connect(self._proc_stopped)
            self.proc.start()

    def _proc_running(self):
        self.state_label.setText("Stav: Aktivní")
        self.state_label.setStyleSheet("color: green;")

    def _proc_stopped(self):
        self.state_label.setText("Stav: Neaktivní")
        self.state_label.setStyleSheet("color: red;")

    def _export_html_splits(self):
        self.pws.append(PreviewWindow(res_html.generate(self.mw.db, True)))

    def _export_html(self):
        self.pws.append(PreviewWindow(res_html.generate(self.mw.db, False)))

    def _export_csv(self):
        fn = QFileDialog.getSaveFileName(
            self,
            "Export výsledků do CSV",
            filter=("CSV (*.csv)"),
        )[0]

        if fn:
            res_csv.export(
                fn,
                self.mw.db,
            )

    def _export_iof_xml(self):
        fn = QFileDialog.getSaveFileName(
            self,
            "Export výsledků do IOF XML 3.0",
            filter=("IOF XML 3.0 (*.xml)"),
        )[0]

        if fn:
            res_xml.export(
                fn,
                self.mw.db,
            )

    def _export_json(self):
        fn = QFileDialog.getSaveFileName(
            self,
            "Export výsledků do ARDF JSON",
            filter=("ARDF JSON (*.json)"),
        )[0]

        if fn:
            data = res_json.export(self.mw.db)
            if not fn.endswith(".json"):
                fn += ".json"
            with open(fn, "w") as f:
                f.write(data)

    def _update_results(self):
        sess = Session(self.mw.db)
        categories = sess.scalars(Select(Category).order_by(Category.name.asc())).all()

        self.results_table.clear()
        self.results_table.setRowCount(0)
        self.results_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.results_table.setColumnCount(5)
        self.results_table.setRowCount(1000)

        row = 0

        for category in categories:
            results_cat = results.calculate_category(self.mw.db, category.name, True)

            if not len(results_cat):
                continue

            cat_name = QTableWidgetItem(category.name)
            f = cat_name.font()
            f.setBold(True)
            f.setPointSize(15)
            cat_name.setFont(f)

            self.results_table.setItem(row, 0, cat_name)
            self.results_table.setSpan(row, 1, 1, 4)

            controls = map(lambda x: x.name, category.controls)
            self.results_table.setItem(row, 1, QTableWidgetItem(", ".join(controls)))

            row += 1

            for person in results_cat:
                if person.place == 0:
                    place = person.status
                else:
                    place = f"{person.place}."

                self.results_table.setItem(row, 0, QTableWidgetItem(place))
                self.results_table.setItem(row, 1, QTableWidgetItem(person.name))
                if person.status not in ["?", "DNS"]:
                    self.results_table.setItem(
                        row, 2, QTableWidgetItem(f"{person.tx} TX")
                    )
                    self.results_table.setItem(
                        row,
                        3,
                        QTableWidgetItem(" - ".join(map(lambda x: x[0], person.order))),
                    )
                    self.results_table.setItem(
                        row,
                        4,
                        QTableWidgetItem(
                            results.format_delta(timedelta(seconds=person.time))
                        ),
                    )

                row += 1
            row += 1

        sess.close()

    def _show(self):
        self._update_results()

        self.results_table.horizontalHeader().hide()
        self.results_table.verticalHeader().hide()

    def closeEvent(self, event) -> None:
        try:
            self.proc.terminate()
            self.proc.wait()
        except:
            ...
        super().closeEvent(event)
