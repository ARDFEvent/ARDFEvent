import pytest
from PySide6.QtCore import Qt
from ui.startnowin import StartNumberWindow
from models import Runner

def test_start_number_assignment(qtbot, fake_mw, session, make_runner, make_category):
    cat1 = make_category(name="Cat1")
    cat2 = make_category(name="Cat2")
    
    r1 = make_runner(category=cat1, name="R1")
    r2 = make_runner(category=cat1, name="R2")
    r3 = make_runner(category=cat2, name="R3")
    
    # Mock startlist_win
    fake_mw.startlist_win = type("MockStartlist", (), {"_update_startlist": lambda self: None})()
    
    # Actually, the lambda was defined as `lambda: None` but it's called as `self.mw.startlist_win._update_startlist()` 
    # where _update_startlist is just a method on the instance, so no 'self' is passed by StartNumberWindow.
    # Wait, the error is `takes 0 positional arguments but 1 was given`. 
    # That means Python IS passing 'self' automatically when calling the lambda as a method on the object.
    
    fake_mw.startlist_win = type("MockStartlist", (), {"_update_startlist": lambda *args: None})()
    
    win = StartNumberWindow(fake_mw)
    qtbot.addWidget(win)
    win._show()
    
    # Verify categories are shown
    assert "Cat1" in win.edits
    assert "Cat2" in win.edits
    
    # Select Cat1 only
    win.edits["Cat1"].setChecked(True)
    win.edits["Cat2"].setChecked(False)
    
    win._assign()
    
    session.refresh(r1)
    session.refresh(r2)
    session.refresh(r3)
    
    assert r1.startno is not None
    assert r2.startno is not None
    assert r3.startno is None
    
    # Ensure they are sequential starting from 1
    startnos = sorted([r1.startno, r2.startno])
    assert startnos == [1, 2]
