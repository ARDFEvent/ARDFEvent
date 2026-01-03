from abc import ABC, abstractmethod


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
        self.mw.welcomewin.helpers_menu.addAction(label, self.on_menu)

    def register_mw_tab(self, widget, icon):
        self.mw._add_page(widget, f"{self.name} {self.version} ({self.author})", icon)
