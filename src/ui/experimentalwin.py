from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, )
from sqlalchemy import Select
from sqlalchemy.orm import Session

from models import Punch


class ExperimentalWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        lay = QVBoxLayout()
        self.setLayout(lay)

        punches_btn = QPushButton(QCoreApplication.translate("ExperimentalWindow", "Opravit ražení"))
        punches_btn.clicked.connect(self._fix_punches)
        lay.addWidget(punches_btn)

    def _fix_punches(self):
        sess = Session(self.mw.db)

        punches = sess.scalars(Select(Punch))

        for punch in punches:
            punch.time = punch.time.replace(microsecond=0)

        sess.commit()
        sess.close()

    def _show(self):
        ...
