import pytest
from PySide6.QtCore import Qt
from sqlalchemy.orm import Session

import models
from ui.categorieswin import CategoriesWindow


def click_list_item(qtbot, list_widget, text):
    for i in range(list_widget.count()):
        item = list_widget.item(i)
        if item.text() == text:
            rect = list_widget.visualItemRect(item)
            qtbot.mouseClick(list_widget.viewport(), Qt.LeftButton, pos=rect.center())
            qtbot.wait(50)
            return
    pytest.fail(f"List item with text '{text}' not found")


def double_click_list_item(qtbot, list_widget, text):
    for i in range(list_widget.count()):
        item = list_widget.item(i)
        if item.text() == text:
            rect = list_widget.visualItemRect(item)
            qtbot.mouseDClick(list_widget.viewport(), Qt.LeftButton, pos=rect.center())

            try:
                list_widget.itemDoubleClicked.emit(item)
            except Exception:
                pass
            qtbot.wait(50)
            return
    pytest.fail(f"List item with text '{text}' not found")


def test_update_and_new_category(qtbot, mw, session, make_category):
    c1 = make_category(name="Alpha")
    c2 = make_category(name="Beta")

    win = CategoriesWindow(mw)
    qtbot.addWidget(win)

    win._update_categories()

    assert win.categories_list.count() == 2
    names = [win.categories_list.item(i).text() for i in range(win.categories_list.count())]
    assert set(names) == {"Alpha", "Beta"}

    session.add(models.Category(name="Gamma", controls=[], display_controls=""))
    session.commit()
    win._update_categories()
    assert win.categories_list.count() == 3
    assert any(win.categories_list.item(i).text() == "Gamma" for i in range(win.categories_list.count()))


def test_select_and_control_lists(qtbot, mw, session, make_category, make_control):
    ctrl1 = make_control(name="C1")
    ctrl2 = make_control(name="C2")

    cat = make_category(name="CatA")

    cat.controls.append(ctrl1)
    session.commit()

    win = CategoriesWindow(mw)
    qtbot.addWidget(win)
    win._update_categories()

    click_list_item(qtbot, win.categories_list, "CatA")

    avail_names = [win.avail_list.item(i).text() for i in range(win.avail_list.count())]
    course_names = [win.course_list.item(i).text() for i in range(win.course_list.count())]

    assert "C1" in avail_names
    assert "C2" in avail_names
    assert "C1" in course_names
    assert "C2" not in course_names


def test_add_and_remove_control(qtbot, mw, session, make_category, make_control):
    ctrl = make_control(name="Extra")
    cat = make_category(name="Cat1")

    win = CategoriesWindow(mw)
    qtbot.addWidget(win)
    win._update_categories()

    click_list_item(qtbot, win.categories_list, "Cat1")

    qtbot.waitUntil(lambda: getattr(win, 'selected', 0) != 0, timeout=500)

    qtbot.wait(50)
    avail_names = [win.avail_list.item(i).text() for i in range(win.avail_list.count())]
    assert "Extra" in avail_names, f"avail_list contents: {avail_names}"

    double_click_list_item(qtbot, win.avail_list, "Extra")

    def has_extra():
        with Session(mw.db) as s:
            cat_db = s.get(models.Category, cat.id)
            return any(c.name == "Extra" for c in cat_db.controls)

    qtbot.waitUntil(has_extra, timeout=500)

    session.refresh(cat)
    assert any(c.name == "Extra" for c in cat.controls)

    double_click_list_item(qtbot, win.course_list, "Extra")
    session.refresh(cat)
    assert all(c.name != "Extra" for c in cat.controls)
