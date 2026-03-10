from enum import Enum
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QTreeWidget, QFormLayout, QVBoxLayout, QPushButton, QTreeWidgetItem, QWidget, \
    QCheckBox, QHeaderView

from ui.previewwin import PreviewWindow


class ReportType(Enum):
    STARTLIST = "STARTOVKA"
    RESULTS = "VÝSLEDKY"
    OTHER = "JINÉ"


class Report:
    def __init__(self, report_type: ReportType, name: str, description: str, source: str, func: Callable, args: dict):
        self.report_type = report_type
        self.name = name
        self.description = description
        self.source = source
        self.func = func
        self.args = args


class ReportWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw
        self.pws = []

        mainlay = QHBoxLayout()
        self.setLayout(mainlay)

        self.report_widget = QTreeWidget()
        self.report_widget.setHeaderLabels(["Typ", "Název", "Popis", "Původ"])
        self.report_widget.itemClicked.connect(self._report_selected)
        header = self.report_widget.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        mainlay.addWidget(self.report_widget)

        rightlay = QVBoxLayout()
        mainlay.addLayout(rightlay)

        self.form_lay = QFormLayout()
        rightlay.addLayout(self.form_lay)

        rightlay.addStretch()

        calc_btn = QPushButton("Generovat")
        calc_btn.clicked.connect(self._generate_report)
        rightlay.addWidget(calc_btn)

    def _show(self):
        self.report_widget.clear()
        for report in sorted(self.mw.reports, key=lambda x: (x.report_type.value, x.name)):
            item = QTreeWidgetItem([report.report_type.value, report.name, report.description, report.source])
            item.setData(0, Qt.UserRole, report)
            self.report_widget.addTopLevelItem(item)

    def _report_selected(self, item: QTreeWidgetItem):
        report: Report = item.data(0, Qt.UserRole)
        for i in range(self.form_lay.rowCount()):
            self.form_lay.removeRow(0)
        for arg_name, arg_type in report.args.items():
            if arg_type == "bool":
                widget = QCheckBox("")
            else:
                widget = QPushButton(f"Neznámý typ {arg_type}")
            self.form_lay.addRow(arg_name, widget)

    def _generate_report(self):
        item = self.report_widget.currentItem()
        if not item:
            return
        report: Report = item.data(0, Qt.UserRole)
        args = []
        for i in range(self.form_lay.rowCount()):
            label = self.form_lay.itemAt(i, QFormLayout.ItemRole.LabelRole).widget().text()
            field = self.form_lay.itemAt(i, QFormLayout.ItemRole.FieldRole).widget()
            if isinstance(field, QCheckBox):
                args.append(field.isChecked())
            else:
                print(f"Neznámý widget {field} pro argument {label}")
                return
        self.pws.append(PreviewWindow(report.func(self.mw.db, *args)))

    def closeEvent(self, event):
        [win.close() for win in self.pws]
