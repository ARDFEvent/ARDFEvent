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


def test_update_and_new_category(qtbot, mw, session, make_category, faker):
    name1 = f"Cat-{faker.random_int(1, 9999)}"
    name2 = f"Cat-{faker.random_int(1, 9999)}"
    c1 = make_category(name=name1)
    c2 = make_category(name=name2)

    win = CategoriesWindow(mw)
    qtbot.addWidget(win)

    win._update_categories()

    assert win.categories_list.count() == 2
    names = [win.categories_list.item(i).text() for i in range(win.categories_list.count())]
    assert set(names) == {name1, name2}

    name3 = f"Cat-{faker.random_int(1, 9999)}"
    session.add(models.Category(name=name3, controls=[], display_controls=""))
    session.commit()
    win._update_categories()
    assert win.categories_list.count() == 3
    assert any(win.categories_list.item(i).text() == name3 for i in range(win.categories_list.count()))


def test_select_and_control_lists(qtbot, mw, session, make_category, make_control, faker):
    name1 = f"Ctrl-{faker.random_int(1, 9999)}"
    name2 = f"Ctrl-{faker.random_int(1, 9999)}"
    ctrl1 = make_control(name=name1)
    ctrl2 = make_control(name=name2)

    cat_name = f"Cat-{faker.random_int(1, 9999)}"
    cat = make_category(name=cat_name)

    cat.controls.append(ctrl1)
    session.commit()

    win = CategoriesWindow(mw)
    qtbot.addWidget(win)
    win._update_categories()

    click_list_item(qtbot, win.categories_list, cat_name)

    avail_names = [win.avail_list.item(i).text() for i in range(win.avail_list.count())]
    course_names = [win.course_list.item(i).text() for i in range(win.course_list.count())]

    assert name1 in avail_names
    assert name2 in avail_names
    assert name1 in course_names
    assert name2 not in course_names


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
