from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

# noinspection PyUnresolvedReferences
from ui import resources_init

if __name__ == "__main__":
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts)

    app = QApplication()
    app.setWindowIcon(QPixmap(":/icons/icon.ico"))

    pixmap = QPixmap(":/icons/splash.png")
    splash = QSplashScreen(pixmap)
    splash.show()
    splash.raise_()
    app.processEvents()

    splash.showMessage("Vytvářím složku...")
    app.processEvents()

    from pathlib import Path
    import time

    rootdir = Path.home() / ".ardfevent"

    if not rootdir.exists():
        rootdir.mkdir()

    try:
        splash.showMessage("Stahuji registraci...")
        app.processEvents()

        import registration

        registration.download()
    except:
        splash.showMessage("Nejste připojeni k internetu - nebyla aktualizována registrace",
                           Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, "red")
        app.processEvents()
        time.sleep(1)

    splash.showMessage("Načítám assety...")
    app.processEvents()

    # noinspection PyUnresolvedReferences
    from ui import resources

    splash.showMessage("Inicializuji UI...")
    app.processEvents()

    import ui.mainwin as mainwin

    win = mainwin.MainWindow()

    splash.showMessage("Vítejte v ARDFEventu!")
    app.processEvents()

    time.sleep(1.5)

    splash.close()
    app.processEvents()

    win.welcomewin.show()

    app.exec()
