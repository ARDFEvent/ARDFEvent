from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget, QLabel, )
from sqlalchemy import Delete, Select
from sqlalchemy.orm import Session

import api
import routes
from models import Category, Control, Runner
from ui.qtaiconbutton import QTAIconButton


class CategoriesWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        mainlay = QHBoxLayout()
        self.setLayout(mainlay)

        leftlay = QVBoxLayout()
        mainlay.addLayout(leftlay)

        buttonslay = QHBoxLayout()
        leftlay.addLayout(buttonslay)

        new_btn = QTAIconButton("mdi6.account-multiple-plus-outline",
                                QCoreApplication.translate("CategoriesWindow", "Nová kategorie"))
        new_btn.clicked.connect(self._new_category)
        buttonslay.addWidget(new_btn)

        delete_btn = QTAIconButton("mdi6.account-multiple-minus-outline",
                                   QCoreApplication.translate("CategoriesWindow", "Smazat kategorii"))
        delete_btn.clicked.connect(self._delete_category)
        buttonslay.addWidget(delete_btn)

        buttonslay.addStretch()

        self.categories_list = QListWidget()
        self.categories_list.itemClicked.connect(self._select)
        leftlay.addWidget(self.categories_list)

        rightlay = QVBoxLayout()
        mainlay.addLayout(rightlay)

        detailslay = QFormLayout()
        rightlay.addLayout(detailslay)

        self.name_edit = QLineEdit()
        self.name_edit.textEdited.connect(self._change)
        detailslay.addRow(QCoreApplication.translate("CategoriesWindow", "Jméno"), self.name_edit)

        self.length_lbl = QLabel("")
        detailslay.addRow(QCoreApplication.translate("CategoriesWindow", "Délka"), self.length_lbl)

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

        category.controls = api.sort_controls(category.controls)

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
            self, QCoreApplication.translate("CategoriesWindow", "Nová kategorie"),
            QCoreApplication.translate("CategoriesWindow", "Zadejte jméno kategorie")
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
            category.controls = api.sort_controls(category.controls)

            for control in sess.scalars(Select(Control)).all():
                self.avail_list.addItem(QListWidgetItem(control.name))

            for control in category.controls:
                self.course_list.addItem(QListWidgetItem(control.name))

            self.length_lbl.setText(routes.get_lenght_str(self.mw.db, category.name))
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
        category.controls = api.sort_controls(category.controls)

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
        category.controls = api.sort_controls(category.controls)

        sess.commit()
        sess.close()

        self._select(QListWidgetItem(name))

    def _show(self):
        self._update_categories()
        self._select(self.categories_list.item(0))
