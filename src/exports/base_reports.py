from PySide6.QtCore import QCoreApplication

import exports.html_results as res_html
import exports.html_startlist as stl_html
import exports.html_startlist_minutes as stl_min_html
from ui.reportwin import Report, ReportType


def register_base_reports(mw):
    mw.reports.append(Report(
        report_type=ReportType.RESULTS,
        name=QCoreApplication.translate("ResultsWindow", "Výsledky"),
        description=QCoreApplication.translate("ResultsWindow", "Výsledky závodu"),
        source="ARDFEvent",
        func=res_html.generate,
        args={"Mezičasy": "bool"}
    ))
    mw.reports.append(Report(
        report_type=ReportType.STARTLIST,
        name=QCoreApplication.translate("ResultsWindow", "Startovka"),
        description=QCoreApplication.translate("ResultsWindow", "Startovka po kategoriích"),
        source="ARDFEvent",
        func=stl_html.generate,
        args={}
    ))
    mw.reports.append(Report(
        report_type=ReportType.STARTLIST,
        name=QCoreApplication.translate("ResultsWindow", "Startovka (min)"),
        description=QCoreApplication.translate("ResultsWindow", "Startovka po minutách"),
        source="ARDFEvent",
        func=stl_min_html.generate,
        args={}
    ))
