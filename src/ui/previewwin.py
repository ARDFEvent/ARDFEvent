from PySide6.QtCore import QCoreApplication
from PySide6.QtGui import QPalette, QColor
from PySide6.QtWidgets import QFileDialog, QPushButton, QVBoxLayout, QWidget, QTextBrowser, QLabel


class PreviewWindow(QWidget):
    def __init__(self, html):
        super().__init__()

        self.html = html

        self.setWindowTitle(QCoreApplication.translate("PreviewWindow", "Náhled"))

        lay = QVBoxLayout()
        self.setLayout(lay)

        lay.addWidget(QLabel("Náhled je pouze orientační. Neodpovídá zejména přesné rozložení na stránce."))

        self.export_btn = QPushButton(QCoreApplication.translate("PreviewWindow", "Exportovat"))
        self.export_btn.clicked.connect(self._export)
        lay.addWidget(self.export_btn)

        self.txtbrs = QTextBrowser()
        self.txtbrs.setHtml(html)
        palette = self.txtbrs.palette()
        palette.setColor(QPalette.Base, QColor("white"))
        palette.setColor(QPalette.Text, QColor("black"))
        self.txtbrs.setPalette(palette)
        lay.addWidget(self.txtbrs)

        self.showMaximized()

    def _export(self):
        fn = QFileDialog.getSaveFileName(
            self,
            QCoreApplication.translate("PreviewWindow", "Exportovat HTML"),
            filter=("HTML (*.html)"),
        )[0]

        if fn:
            if not fn.endswith(".html"):
                fn += ".html"
            with open(fn, "w", encoding="utf-8") as f:
                f.write(self.html)
            self.close()
