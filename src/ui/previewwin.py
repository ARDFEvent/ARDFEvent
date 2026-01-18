from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QFileDialog, QPushButton, QVBoxLayout, QWidget


class PreviewWindow(QWidget):
    def __init__(self, html):
        super().__init__()

        self.html = html

        self.setWindowTitle("Náhled")

        lay = QVBoxLayout()
        self.setLayout(lay)

        self.export_btn = QPushButton("Exportovat")
        self.export_btn.clicked.connect(self._export)
        lay.addWidget(self.export_btn)

        self.webview = QWebEngineView()
        self.webview.setHtml(html)
        lay.addWidget(self.webview)

        self.show()

    def _export(self):
        fn = QFileDialog.getSaveFileName(
            self,
            "Export HTML",
            filter=("HTML (*.html)"),
        )[0]

        if fn:
            if not fn.endswith(".html"):
                fn += ".html"
            with open(fn, "w", encoding="utf-8") as f:
                f.write(self.html)
            self.close()
