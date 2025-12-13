import shutil
from pathlib import Path

from dulwich import porcelain
from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWizard,
    QWizardPage,
)

import api


class IntroPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Nastavení/Setup")
        layout = QVBoxLayout()
        self.setLayout(layout)
        lbl = QLabel(
            "Vítejte v průvodci nastavením ARDFEvent. Tento průvodce vám pomůže nakonfigurovat základní nastavení aplikace.\n\nWelcome to the ARDFEvent Setup Wizard. This wizard will help you configure the basic settings of the application."
        )
        lbl.setWordWrap(True)
        layout.addWidget(lbl)


class LanguagePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Výběr jazyka/Language Selection")
        layout = QVBoxLayout()
        self.setLayout(layout)
        lbl = QLabel("Vyberte jazyk.\nSelect your language.")
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        self.english_radio = QRadioButton("Angličtina (English)")
        self.czech_radio = QRadioButton("Čeština (Czech)")
        layout.addWidget(self.english_radio)
        layout.addWidget(self.czech_radio)
        self.english_radio.toggled.connect(lambda _=None: self.completeChanged.emit())
        self.czech_radio.toggled.connect(lambda _=None: self.completeChanged.emit())
        self.isComplete = (
            lambda: self.english_radio.isChecked() or self.czech_radio.isChecked()
        )
        layout.addStretch()
        lbl = QLabel(
            "Program se restartuje a nastavení bude pokračovat.\nThe program will restart and the setup will continue."
        )
        lbl.setWordWrap(True)
        layout.addWidget(lbl)

    def validatePage(self):
        api.set_config_value("lang", "en" if self.english_radio.isChecked() else "cs")
        return True


class DefaultPluginPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle(QCoreApplication.translate("SetupWizard", "Výchozí pluginy"))
        layout = QVBoxLayout()
        self.setLayout(layout)
        lbl = QLabel(
            QCoreApplication.translate(
                "SetupWizard", "Vyberte výchozí pluginy, které chcete nainstalovat."
            )
        )
        lbl.setWordWrap(True)
        layout.addWidget(lbl)
        self.robis_chk = QCheckBox("ROBis")
        self.stage_chk = QCheckBox(
            QCoreApplication.translate("SetupWizard", "Etapový závod")
        )
        layout.addWidget(self.robis_chk)
        layout.addWidget(self.stage_chk)
        layout.addStretch()
        layout.addWidget(
            QLabel(
                QCoreApplication.translate("SetupWizard", "Program na chvilku zamrzne.")
            )
        )

    def validatePage(self):
        try:
            shutil.rmtree(str((Path.home() / ".ardfevent" / "plugins").absolute()))
        except:
            pass
        if not (Path.home() / ".ardfevent" / "plugins").exists():
            (Path.home() / ".ardfevent" / "plugins").mkdir(parents=True)
        urls = [
            "https://github.com/jacobczsk/ARDFEvent_robisplugin",
            "https://github.com/jacobczsk/ARDFEvent_stagesplugin",
        ]
        for url, chk in zip(urls, [self.robis_chk, self.stage_chk]):
            if chk.isChecked():
                porcelain.clone(
                    url,
                    Path.home()
                    / ".ardfevent"
                    / "plugins"
                    / url.split("/")[-1].replace(".git", ""),
                )
        return True


class EndPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle(QCoreApplication.translate("SetupWizard", "Dokončení"))
        layout = QVBoxLayout()
        self.setLayout(layout)
        lbl = QLabel(
            QCoreApplication.translate("SetupWizard", "Nastavení je dokončeno.")
        )
        lbl.setWordWrap(True)
        layout.addWidget(lbl)


class SetupWizard(QWizard):
    def __init__(self, part):
        super().__init__()
        self.setWindowTitle("ARDFEvent")
        if not part:
            self.addPage(IntroPage())
            self.addPage(LanguagePage())
        else:
            self.addPage(DefaultPluginPage())
