from datetime import datetime

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy import Select
from sqlalchemy.orm import Session
from yaml import dump, load

from models import Punch, Runner

try:
    from yaml import CDumper as Dumper
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Dumper, Loader


class OCheckListWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        lay = QVBoxLayout()
        self.setLayout(lay)

        btn_lay = QHBoxLayout()
        lay.addLayout(btn_lay)

        import_btn = QPushButton("Importovat start-status.yaml")
        import_btn.clicked.connect(self._import)
        btn_lay.addWidget(import_btn)

        btn_lay.addStretch()

        self.log = QTextBrowser()
        lay.addWidget(self.log)

    def _show(self):
        self.log.clear()

    def _import(self):
        fn = QFileDialog.getOpenFileName(
            self,
            "Importovat z OCheckList",
            filter=("OCheckList YAML (*.yaml)"),
        )[0]

        if not fn:
            return

        sess = Session(self.mw.db)

        with open(fn) as f:
            data = load(f, Loader=Loader)["Data"]
            for runner_base in data:
                runner = runner_base["Runner"]
                runner_id = int(runner["Id"])
                runner_db = sess.scalars(
                    Select(Runner).where(Runner.id == runner_id)
                ).one_or_none()

                if not runner_db:
                    continue
                elif runner_db.ocheck_processed:
                    continue

                if runner["StartStatus"] == "DNS":
                    self.log.append(f"{runner_db.name}: DNS")
                    runner_db.manual_dns = True

                if "NewCard" in runner:
                    self.log.append(
                        f"{runner_db.name}: SI {runner_db.si} => {runner["NewCard"]}"
                    )
                    runner_db.si = runner["NewCard"]

        sess.commit()
        sess.close()
