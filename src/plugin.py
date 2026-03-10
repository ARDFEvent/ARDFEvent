from abc import ABC, abstractmethod
from typing import Callable

from ui.reportwin import Report, ReportType


class Plugin(ABC):
    name: str
    author: str
    version: str

    def __init__(self, mw):
        self.mw = mw

    @abstractmethod
    def on_startup(self):
        pass

    @abstractmethod
    def on_readout(self, sinum: int):
        pass

    @abstractmethod
    def on_menu(self):
        pass

    def register_ww_menu(self, label):
        self.mw.plug_menu.addAction(label, self.on_menu)

    def register_mw_tab(self, widget, icon):
        self.mw._add_page(widget, f"{self.name} {self.version} ({self.author})", icon)

    def register_report(self, report_type: ReportType, name: str, description: str, source: str, func: Callable,
                        args: dict):
        self.mw.reports.append(Report(
            report_type=report_type,
            name=name,
            description=description,
            source=source,
            func=func,
            args=args
        ))
