import faulthandler

faulthandler.enable()

import os
import sys
import warnings

import certifi
from PySide6.QtCore import Qt, QCoreApplication, QTranslator, QLocale
from PySide6.QtGui import QPixmap, QFontDatabase
from PySide6.QtWidgets import QApplication, QSplashScreen, QWizard

import api
import pluginmanager
# noinspection PyUnresolvedReferences
from ui import resources_init

LANGUAGES = {
    "en": QLocale.Language.English,
    "cs": QLocale.Language.Czech,
}

if __name__ == "__main__":
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

    warnings.filterwarnings("ignore")

    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

    app = QApplication()
    app.setApplicationName("ARDFEvent")
    app.setOrganizationName("JJ")
    app.setWindowIcon(QPixmap(":/icons/icon.ico"))

    pixmap = QPixmap(":/icons/splash.png")
    splash = QSplashScreen(pixmap)
    splash.show()
    splash.raise_()
    app.processEvents()

    translator = QTranslator()
    if translator.load(
            QLocale(LANGUAGES[api.get_config_value("lang", "cs")]),
            "ARDFEvent_",
            "",
            ":/i18n",
    ):
        app.installTranslator(translator)

    splash.showMessage(QCoreApplication.translate("Loading", "Vytvářím složku..."))
    app.processEvents()

    from pathlib import Path
    import time

    rootdir = Path.home() / ".ardfevent"

    if not rootdir.exists():
        rootdir.mkdir()

    if not (rootdir / "plugins").exists():
        (rootdir / "plugins").mkdir()

    try:
        splash.showMessage(
            QCoreApplication.translate("Loading", "Stahuji registraci...")
        )
        app.processEvents()

        import registration

        registration.download()
    except:
        splash.showMessage(
            QCoreApplication.translate(
                "Loading",
                "Nejste připojeni k internetu - nebyla aktualizována registrace",
            ),
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft,
            "red",
        )
        app.processEvents()
        time.sleep(1)

    splash.showMessage(QCoreApplication.translate("Loading", "Načítám assety..."))
    app.processEvents()

    # noinspection PyUnresolvedReferences
    from ui import resources

    QFontDatabase.addApplicationFont(":/font/SpaceMono.ttf")
    app.setFont("Space Mono")

    splash.showMessage(QCoreApplication.translate("Loading", "Inicializuji UI..."))
    app.processEvents()

    import ui.mainwin as mainwin

    win = mainwin.MainWindow()

    pl = pluginmanager.PluginManager(win)
    win.pl = pl
    for status, plugin in pl.load():
        if status:
            splash.showMessage(
                QCoreApplication.translate("Loading", "Načten %s") % plugin["name"]
            )
            app.processEvents()
        else:
            splash.showMessage(
                QCoreApplication.translate(
                    "Loading", "Plugin %s nenačten - nelze ověřit podpis."
                )
                % plugin["name"]
            )
            app.processEvents()
            time.sleep(1)

    splash.showMessage(QCoreApplication.translate("Loading", "Vítejte v ARDFEventu!"))
    app.processEvents()

    time.sleep(1)

    splash.close()
    app.processEvents()

    if not api.get_config_value("setup_completed", False):
        from ui.setupwiz import SetupWizard

        wiz = SetupWizard(api.get_config_value("setup_part", False))

        if wiz.exec() == QWizard.Accepted:
            api.set_config_value(
                "setup_completed", api.get_config_value("setup_part", False)
            )
            api.set_config_value("setup_part", True)

            executable = sys.executable
            executable_filename = os.path.split(executable)[1]
            if executable_filename.lower().startswith("python"):
                python = executable
                os.execv(
                    python,
                    [
                        python,
                    ]
                    + sys.argv,
                )

            else:
                os.execv(executable, sys.argv)

        sys.exit(0)

    win.showMaximized()

    app.exec()
