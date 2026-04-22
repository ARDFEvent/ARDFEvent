import pytest
from PySide6.QtWidgets import QCheckBox, QFormLayout
from ui.reportwin import ReportWindow, Report, ReportType
from types import SimpleNamespace

def test_report_window_shows_reports(qtbot, fake_mw):
    # Mock report
    def dummy_func(db): return "<html></html>"
    report = Report(ReportType.OTHER, "Test Report", "Description", "Source", dummy_func, {})
    fake_mw.reports = [report]
    
    win = ReportWindow(fake_mw)
    qtbot.addWidget(win)
    win._show()
    
    assert win.report_widget.topLevelItemCount() == 1
    assert win.report_widget.topLevelItem(0).text(1) == "Test Report"

def test_report_arguments(qtbot, fake_mw):
    def dummy_func(db, arg1): return "<html></html>"
    # Arguments: {"BooleanParam": "bool"}
    report = Report(ReportType.OTHER, "Param Report", "Desc", "Src", dummy_func, {"BooleanParam": "bool"})
    fake_mw.reports = [report]
    
    win = ReportWindow(fake_mw)
    qtbot.addWidget(win)
    win._show()
    
    # Select report
    item = win.report_widget.topLevelItem(0)
    win._report_selected(item)
    
    # Check if checkbox was created
    assert win.form_lay.rowCount() == 1
    # QFormLayout.itemAt(row, role) - role 1 is FieldRole
    assert isinstance(win.form_lay.itemAt(0, QFormLayout.FieldRole).widget(), QCheckBox)
