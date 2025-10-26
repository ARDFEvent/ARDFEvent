from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QCheckBox, QVBoxLayout
from sqlalchemy import Select
from sqlalchemy.orm import Session

from models import Category, Runner


class StartNumberWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        self.mainlay = QVBoxLayout()
        self.setLayout(self.mainlay)
        self.setWindowTitle("Přiřazení startovních čísel")

        self.draw_btn = QPushButton("Přiřadit")
        self.draw_btn.clicked.connect(self._assign)
        self.mainlay.addWidget(self.draw_btn)

        self.mainlay.addWidget(QLabel("Má startovní čísla?"))

        self.edits = {}

    def _assign(self):
        with Session(self.mw.db) as sess:
            i = 1
            for cat_name, edit in self.edits.items():
                if edit.isChecked():
                    runners = sess.scalars(Select(Runner).where(Runner.category.has(Category.name == cat_name)))
                    for runner in runners:
                        runner.startno = i
                        i += 1
            sess.commit()
        self.close()

    def show(self):
        self._show()
        super().show()

    def _show(self):
        for edit in self.edits.values():
            self.mainlay.removeWidget(edit)

        with Session(self.mw.db) as sess:
            categories = sess.scalars(Select(Category)).all()

            for cat in categories:
                if not len(
                        sess.scalars(Select(Runner).where(Runner.category == cat)).all()
                ):
                    continue

                cat_edit = QCheckBox(cat.name)

                self.mainlay.addWidget(cat_edit)
                self.edits[cat.name] = cat_edit
