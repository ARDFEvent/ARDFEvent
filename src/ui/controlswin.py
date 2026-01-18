from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import Delete, Select
from sqlalchemy.orm import Session

from models import Control


class ControlsWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw
        self.setWindowTitle("Kontroly")

        mainlay = QVBoxLayout()
        self.setLayout(mainlay)

        mainlay.addWidget(QLabel("Přednastavené kontroly:"))

        presetslay = QHBoxLayout()
        mainlay.addLayout(presetslay)

        slowcontrols_preset = QPushButton("Pomalé kontroly (1-5 + M)")
        slowcontrols_preset.clicked.connect(self._preset_slow)
        presetslay.addWidget(slowcontrols_preset)

        allcontrols_preset = QPushButton("Všechny kontroly (1-5 + R1-R5 + M)")
        allcontrols_preset.clicked.connect(self._preset_all)
        presetslay.addWidget(allcontrols_preset)

        sprint_preset = QPushButton("Sprint (1-5 + S + R1-R5 + M)")
        sprint_preset.clicked.connect(self._preset_sprint)
        presetslay.addWidget(sprint_preset)

        operationslay = QHBoxLayout()
        mainlay.addLayout(operationslay)

        add_btn = QPushButton("Přidat")
        add_btn.clicked.connect(self._new_control)
        operationslay.addWidget(add_btn)

        save_btn = QPushButton("Uložit")
        save_btn.clicked.connect(self._save)
        operationslay.addWidget(save_btn)

        delete_btn = QPushButton("Smazat")
        delete_btn.clicked.connect(self._delete)
        operationslay.addWidget(delete_btn)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Jméno", "SI kód", "Povinná", "Divácká"])
        self.table.itemClicked.connect(self._set_last)

        mainlay.addWidget(self.table, 1)

        self.last_selected = None

    def _set_last(self, item: QTableWidgetItem):
        self.last_selected = item

    def _delete(self):
        self.table.removeRow(self.last_selected.row())

    def _set_controls(self, controls):
        sess = Session(self.mw.db)
        sess.execute(Delete(Control))
        sess.add_all(controls)
        sess.commit()
        sess.close()

    def _preset_slow(self):
        self._set_controls(
            [
                Control(name="1", code=31, mandatory=False, spectator=False),
                Control(name="2", code=32, mandatory=False, spectator=False),
                Control(name="3", code=33, mandatory=False, spectator=False),
                Control(name="4", code=34, mandatory=False, spectator=False),
                Control(name="5", code=35, mandatory=False, spectator=False),
                Control(name="M", code=99, mandatory=True, spectator=False),
            ]
        )
        self._update_table()

    def _preset_all(self):
        self._set_controls(
            [
                Control(name="1", code=31, mandatory=False, spectator=False),
                Control(name="2", code=32, mandatory=False, spectator=False),
                Control(name="3", code=33, mandatory=False, spectator=False),
                Control(name="4", code=34, mandatory=False, spectator=False),
                Control(name="5", code=35, mandatory=False, spectator=False),
                Control(name="R1", code=41, mandatory=False, spectator=False),
                Control(name="R2", code=42, mandatory=False, spectator=False),
                Control(name="R3", code=43, mandatory=False, spectator=False),
                Control(name="R4", code=44, mandatory=False, spectator=False),
                Control(name="R5", code=45, mandatory=False, spectator=False),
                Control(name="M", code=99, mandatory=True, spectator=False),
            ]
        )
        self._update_table()

    def _preset_sprint(self):
        self._set_controls(
            [
                Control(name="1", code=31, mandatory=False, spectator=False),
                Control(name="2", code=32, mandatory=False, spectator=False),
                Control(name="3", code=33, mandatory=False, spectator=False),
                Control(name="4", code=34, mandatory=False, spectator=False),
                Control(name="5", code=35, mandatory=False, spectator=False),
                Control(name="R1", code=41, mandatory=False, spectator=False),
                Control(name="R2", code=42, mandatory=False, spectator=False),
                Control(name="R3", code=43, mandatory=False, spectator=False),
                Control(name="R4", code=44, mandatory=False, spectator=False),
                Control(name="R5", code=45, mandatory=False, spectator=False),
                Control(name="S", code=46, mandatory=True, spectator=True),
                Control(name="M", code=99, mandatory=True, spectator=False),
            ]
        )
        self._update_table()

    def _save(self):
        controls = []

        for i in range(self.table.rowCount()):
            name = self.table.item(i, 0).text()
            if name == "":
                continue

            try:
                code = int(self.table.item(i, 1).text())
            except:
                code = -1
            mandatory = self.table.item(i, 2).checkState() == Qt.CheckState.Checked
            spectator = self.table.item(i, 3).checkState() == Qt.CheckState.Checked
            controls.append(
                Control(name=name, code=code, mandatory=mandatory, spectator=spectator)
            )

        self._set_controls(controls)
        self._update_table()

    def _new_control(self):
        self._add_control(
            Control(name="", code=-1, mandatory=False, spectator=False),
            self.table.rowCount(),
        )

    def _remove_control(self):
        self.table.removeRow(self.table.selectedRanges()[0].topRow())

    def _add_control(self, control: Control, i: int):
        self.table.setRowCount(self.table.rowCount() + 1)

        it_name = QTableWidgetItem(control.name)
        it_name.setFlags(Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled)
        self.table.setItem(i, 0, it_name)

        it_code = QTableWidgetItem(str(control.code))
        it_code.setFlags(Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsEnabled)
        self.table.setItem(i, 1, it_code)

        it_mandatory = QTableWidgetItem()
        it_mandatory.setFlags(
            Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
        )

        if control.mandatory:
            it_mandatory.setCheckState(Qt.CheckState.Checked)
        else:
            it_mandatory.setCheckState(Qt.CheckState.Unchecked)

        self.table.setItem(i, 2, it_mandatory)

        it_spectator = QTableWidgetItem()
        it_spectator.setFlags(
            Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled
        )

        if control.spectator:
            it_spectator.setCheckState(Qt.CheckState.Checked)
        else:
            it_spectator.setCheckState(Qt.CheckState.Unchecked)

        self.table.setItem(i, 3, it_spectator)

    def _update_table(self):
        sess = Session(self.mw.db)
        controls = sess.scalars(Select(Control)).all()

        self.table.setRowCount(0)

        i = 0
        for control in controls:
            self._add_control(control, i)
            i += 1

        sess.close()

    def _show(self):
        self._update_table()
