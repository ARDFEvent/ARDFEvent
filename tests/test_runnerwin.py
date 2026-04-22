import pytest
from PySide6.QtCore import Qt
from ui.runnerwin import RunnerWindow
from models import Runner

from types import SimpleNamespace

def test_runner_window_creation(qtbot, fake_mw, session, make_runner):
    runner = make_runner(name="Test Runner")
    fake_mw.import_win = SimpleNamespace(show=lambda: None)
    win = RunnerWindow(fake_mw)
    qtbot.addWidget(win)
    win._show()
    
    assert win.runners_list.count() == 1
    assert win.runners_list.item(0).text() == "Test Runner"
    assert win.name_edit.text() == "Test Runner"

def test_save_runner(qtbot, fake_mw, session, make_runner, faker):
    runner = make_runner(name="Original Name")
    fake_mw.import_win = SimpleNamespace(show=lambda: None)
    win = RunnerWindow(fake_mw)
    qtbot.addWidget(win)
    win._show()
    
    new_name = faker.name()
    win.name_edit.setText(new_name)
    win._save_runner()
    
    session.refresh(runner)
    assert runner.name == new_name
