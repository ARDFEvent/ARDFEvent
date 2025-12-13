from datetime import datetime

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import (
    QComboBox,
    QDateTimeEdit,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QWidget, )
from dateutil.parser import parser

import api


class BasicInfoWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        lay = QFormLayout()
        self.setLayout(lay)

        self.name_edit = QLineEdit()
        lay.addRow(QCoreApplication.translate("BasicInfoWindow", "Jméno"), self.name_edit)

        self.date_edit = QDateTimeEdit()
        self.date_edit.setDisplayFormat("dd. MM. yyyy HH:mm")
        lay.addRow(QCoreApplication.translate("BasicInfoWindow", "Datum a čas"), self.date_edit)

        self.org_edit = QLineEdit()
        lay.addRow(QCoreApplication.translate("BasicInfoWindow", "Pořadatel"), self.org_edit)

        self.limit_edit = QSpinBox()
        self.limit_edit.setRange(0, 10000)
        lay.addRow(QCoreApplication.translate("BasicInfoWindow", "Limit"), self.limit_edit)

        self.band_select = QComboBox()
        self.band_select.addItems(api.BANDS)
        lay.addRow(QCoreApplication.translate("BasicInfoWindow", "Pásmo"), self.band_select)

        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self._on_ok)
        lay.addRow(self.ok_btn)

    def _on_ok(self):
        api.set_basic_info(
            self.mw.db,
            {
                "name": self.name_edit.text(),
                "date_tzero": self.date_edit.dateTime()
                .toPython()
                .replace(second=0)
                .isoformat(),
                "organizer": self.org_edit.text(),
                "limit": str(self.limit_edit.value()),
                "band": self.band_select.currentText(),
            },
        )

    def _show(self):
        basic_info = api.get_basic_info(self.mw.db)

        if basic_info["name"]:
            self.name_edit.setText(basic_info["name"])

        if basic_info["date_tzero"]:
            self.date_edit.setDateTime(parser().parse(basic_info["date_tzero"]))
        else:
            self.date_edit.setDateTime(datetime(2025, 1, 1, 10))

        if basic_info["organizer"]:
            self.org_edit.setText(basic_info["organizer"])

        if basic_info["limit"]:
            self.limit_edit.setValue(int(basic_info["limit"]))

        if basic_info["band"] in api.BANDS:
            self.band_select.setCurrentIndex(api.BANDS.index(basic_info["band"]))
