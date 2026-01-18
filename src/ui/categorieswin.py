from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import Delete, Select
from sqlalchemy.orm import Session

from models import Category, Control, Runner


class CategoriesWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        mainlay = QHBoxLayout()
        self.setLayout(mainlay)

        self.categories_list = QListWidget()
        self.categories_list.itemClicked.connect(self._select)
        mainlay.addWidget(self.categories_list)

        rightlay = QVBoxLayout()
        mainlay.addLayout(rightlay)

        buttonslay = QHBoxLayout()
        rightlay.addLayout(buttonslay)

        new_btn = QPushButton("Nová kategorie")
        new_btn.clicked.connect(self._new_category)
        buttonslay.addWidget(new_btn)

        delete_btn = QPushButton("Smazat kategorii")
        delete_btn.clicked.connect(self._delete_category)
        buttonslay.addWidget(delete_btn)

        detailslay = QFormLayout()
        rightlay.addLayout(detailslay)

        self.name_edit = QLineEdit()
        self.name_edit.textEdited.connect(self._change)
        detailslay.addRow("Jméno", self.name_edit)

        self.display_controls_edit = QLineEdit()
        self.display_controls_edit.textEdited.connect(self._change)
        detailslay.addRow(
            "Před závodem zobrazené kontroly (startovka, ...)",
            self.display_controls_edit,
        )

        listslayout = QHBoxLayout()
        rightlay.addLayout(listslayout)

        self.avail_list = QListWidget()
        self.avail_list.itemDoubleClicked.connect(self._add_control)
        listslayout.addWidget(self.avail_list)

        self.course_list = QListWidget()
        self.course_list.itemDoubleClicked.connect(self._remove_control)
        listslayout.addWidget(self.course_list)

        self.selected = 0

    def _remove_control(self, item: QListWidgetItem):
        sess = Session(self.mw.db)

        category = sess.scalar(Select(Category).where(Category.id == self.selected))
        for control in category.controls:
            if control.name == item.text():
                category.controls.remove(control)
                break

        name = category.name

        sess.commit()
        sess.close()

        self._select(QListWidgetItem(name))

    def _delete_category(self):
        sess = Session(self.mw.db)
        sess.execute(Delete(Category).where(Category.id == self.selected))
        sess.execute(Delete(Runner).where(Runner.category_id == self.selected))
        sess.commit()

        self._update_categories()
        self._select(self.categories_list.item(0))
        sess.close()

    def _update_categories(self):
        self.categories_list.clear()

        sess = Session(self.mw.db)
        categories = list(
            sess.scalars(Select(Category).order_by(Category.name.asc())).all()
        )

        for category in categories:
            self.categories_list.addItem(QListWidgetItem(category.name))

        sess.close()

    def _new_category(self):
        name, ok = QInputDialog.getText(
            self, "Nová kategorie", "Zadejte jméno kategorie"
        )

        if not ok:
            return

        sess = Session(self.mw.db)
        sess.add(Category(name=name, controls=[], display_controls=""))
        sess.commit()
        sess.close()

        self._update_categories()

    def _select(self, item: QListWidgetItem):
        self.avail_list.clear()
        self.course_list.clear()

        sess = Session(self.mw.db)

        try:
            category = sess.scalars(
                Select(Category).where(Category.name == item.text())
            ).one_or_none()

            if not category:
                sess.close()
                return

            self.selected = category.id

            self.name_edit.setText(category.name)
            self.display_controls_edit.setText(category.display_controls)

            for control in sess.scalars(Select(Control)).all():
                self.avail_list.addItem(QListWidgetItem(control.name))

            for control in category.controls:
                self.course_list.addItem(QListWidgetItem(control.name))
        except:
            ...

        sess.close()

    def _change(self):
        sess = Session(self.mw.db)
        category = sess.scalars(
            Select(Category).where(Category.id == self.selected)
        ).one_or_none()

        if not category:
            return

        category.name = self.name_edit.text()
        category.display_controls = self.display_controls_edit.text()

        sess.commit()
        sess.close()

        self._update_categories()

    def _add_control(self, item: QListWidgetItem):
        sess = Session(self.mw.db)
        category = sess.scalars(
            Select(Category).where(Category.id == self.selected)
        ).one_or_none()

        control = sess.scalars(
            Select(Control).where(Control.name == item.text())
        ).one_or_none()

        if not (category and control):
            sess.close()
            return

        category.controls.append(control)

        name = category.name

        category.display_controls = ", ".join(map(lambda x: x.name, category.controls))

        sess.commit()
        sess.close()

        self._select(QListWidgetItem(name))

    def _show(self):
        self._update_categories()
        self._select(self.categories_list.item(0))
