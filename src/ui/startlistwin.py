from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import Select
from sqlalchemy.orm import Session

import exports.html_startlist as stl_html
import exports.html_startlist_minutes as stl_min_html
import exports.robis_csv_startlist as stl_robis_csv
import exports.xml_startlist as stl_xml
from models import Runner
from ui.previewwin import PreviewWindow


class StartlistWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw
        self.pws = []

        lay = QVBoxLayout()
        self.setLayout(lay)

        btn_lay = QHBoxLayout()
        lay.addLayout(btn_lay)

        export_menu = QMenu(self)
        export_menu.addAction("HTML po kategoriích", self._export_html)
        export_menu.addAction("HTML po minutách", self._export_html_minutes)
        export_menu.addAction("CSV pro ROBis", self._export_robis_csv)
        export_menu.addAction("IOF XML 3.0", self._export_iof_xml)

        export_btn = QPushButton("Exportovat")
        export_btn.setMenu(export_menu)
        btn_lay.addWidget(export_btn)

        draw_win_btn = QPushButton("Losovat startovku")
        draw_win_btn.clicked.connect(self.mw.startlistdraw_win.show)
        btn_lay.addWidget(draw_win_btn)

        btn_lay.addStretch()

        self.startlist_table = QTableWidget()
        self.startlist_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.startlist_table)

    def _export_html(self):
        self.pws.append(PreviewWindow(stl_html.generate(self.mw.db)))

    def _export_html_minutes(self):
        self.pws.append(PreviewWindow(stl_min_html.generate(self.mw.db)))

    def _export_robis_csv(self):
        fn = QFileDialog.getSaveFileName(
            self,
            "Export startovky do CSV pro ROBis",
            filter=("ROBis CSV (*.csv)"),
        )[0]

        if fn:
            stl_robis_csv.export(
                fn,
                self.mw.db,
            )

    def _export_iof_xml(self):
        fn = QFileDialog.getSaveFileName(
            self,
            "Export startovky do IOF XML 3.0",
            filter=("IOF XML 3.0 (*.xml)"),
        )[0]

        if fn:
            stl_xml.export(
                fn,
                self.mw.db,
            )

    def _update_startlist(self):
        sess = Session(self.mw.db)

        self.startlist_table.setSortingEnabled(True)
        self.startlist_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        self.startlist_table.clear()
        self.startlist_table.setColumnCount(5)
        self.startlist_table.setHorizontalHeaderLabels(
            ["Čas startu", "Jméno", "Kategorie", "Index", "SI"]
        )
        self.startlist_table.setRowCount(1000)

        row = 0

        for person in sess.scalars(Select(Runner)).all():
            starttime = person.startlist_time
            if starttime is None:
                starttime = "-"
            else:
                starttime = starttime.strftime("%H:%M:%S")
            self.startlist_table.setItem(row, 0, QTableWidgetItem(starttime))
            self.startlist_table.setItem(row, 1, QTableWidgetItem(person.name))
            self.startlist_table.setItem(row, 2, QTableWidgetItem(person.category.name))
            self.startlist_table.setItem(row, 3, QTableWidgetItem(person.reg))
            self.startlist_table.setItem(row, 4, QTableWidgetItem(str(person.si)))

            row += 1

        sess.close()

    def _show(self):
        self._update_startlist()

        self.startlist_table.verticalHeader().hide()
