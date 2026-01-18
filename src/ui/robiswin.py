import json
from datetime import datetime, timedelta

import requests
from dateutil.parser import parser
from PySide6.QtCore import QByteArray, QUrl, Slot
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextBrowser,
    QWidget,
)
from sqlalchemy import Delete, Select
from sqlalchemy.orm import Session

import api
import results
from exports import json_results as res_json
from models import Category, Runner


class ROBisWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        lay = QFormLayout()
        self.setLayout(lay)

        self.api_edit = QLineEdit()
        lay.addRow("API klíč", self.api_edit)

        self.id_edit = QSpinBox()
        self.id_edit.setRange(0, 10000)
        lay.addRow("ID soutěže", self.id_edit)

        self.etap_edit = QSpinBox()
        self.etap_edit.setRange(0, 10000)
        lay.addRow("Číslo etapy (EX)", self.etap_edit)

        self.ok_btn = QPushButton("OK")
        self.ok_btn.clicked.connect(self._on_ok)
        lay.addRow(self.ok_btn)

        lay.addRow(QLabel(""))

        self.download_btn = QPushButton(
            "Stáhnout přihlášky, kategorie - Pozor! Tato akce smaže všechny stávající závodníky!"
        )
        self.download_btn.clicked.connect(self._download)
        lay.addRow(self.download_btn)

        self.update_btn = QPushButton("Aktualizovat všechny online výsledky")
        self.update_btn.clicked.connect(
            lambda: self._send_online_readout(self.mw.db, 0, True)
        )
        lay.addRow(self.update_btn)

        self.upload_btn = QPushButton("Nahrát výsledky")
        self.upload_btn.clicked.connect(self._upload)
        lay.addRow(self.upload_btn)

        lay.addRow(QLabel(""))

        self.log = QTextBrowser()
        lay.addWidget(self.log)

        self.nmmanager = QNetworkAccessManager(self)
        self.nmmanager.finished.connect(self.handle_online_res_reply)

    def _on_ok(self):
        api.set_basic_info(
            self.mw.db,
            {
                "robis_api": self.api_edit.text(),
                "robis_id": self.id_edit.text(),
                "robis_etap": self.etap_edit.text(),
            },
        )

    def _show(self):
        basic_info = api.get_basic_info(self.mw.db)
        self.api_edit.setText(basic_info["robis_api"])
        self.id_edit.setValue(int(basic_info["robis_id"]))
        self.etap_edit.setValue(int(basic_info["robis_etap"]))

    def _upload(self):
        response = requests.post(
            "https://rob-is.cz/api/results/?valid=True",
            res_json.export(self.mw.db),
            headers={
                "Race-Api-Key": self.api_edit.text(),
                "Content-Type": "application/json",
            },
        )

        self.log.append(
            f"{datetime.now().strftime("%H:%M:%S")} - Finální výsledky: {response.status_code} {response.text}"
        )

    def _download(self):
        response = requests.get(
            f"https://rob-is.cz/api/?type=json&name=event&event_id={self.id_edit.value()}",
            headers={"Race-Api-Key": self.api_edit.text()},
        )
        if response.status_code != 200:
            QMessageBox.critical(
                self,
                "Chyba",
                f"Stahování se nezdařilo: {response.status_code} {response.text}",
            )
            return
        props = response.json()["properties"]
        race = props["races"][self.etap_edit.value() - 1]

        limit_str = race["race_time_limit"].split(":")
        limit = int(limit_str[0]) * 60 + int(limit_str[1])

        api.set_basic_info(
            self.mw.db,
            {
                "name": props["event_name"] + " - " + race["race_name"],
                "date_tzero": parser().parse(race["race_start"]).isoformat(),
                "organizer": props["event_organiser"],
                "limit": limit,
                "band": api.BANDS[["M2", "M80", "COMBINED"].index(race["race_band"])],
            },
        )

        sess = Session(self.mw.db)
        sess.execute(Delete(Runner))

        for cat in race["categories"]:
            if not len(
                sess.scalars(
                    Select(Category).where(Category.name == cat["category_name"])
                ).all()
            ):
                sess.add(
                    Category(
                        name=cat["category_name"], controls=[], display_controls=""
                    )
                )
                self.log.append(
                    f"{datetime.now().strftime('%H:%M:%S')} - Přidávám kategorii {cat['category_name']}"
                )

        for runner in race["competitors"]:
            sess.add(
                Runner(
                    name=runner["last_name"] + ", " + runner["first_name"],
                    club=runner["competitor_club"],
                    si=runner["si_number"] or 0,
                    reg=runner["competitor_index"],
                    category=sess.scalars(
                        Select(Category).where(
                            Category.name == runner["competitor_category"]
                        )
                    ).first(),
                    call="",
                )
            )
        sess.commit()
        sess.close()

        self.log.append(f"{datetime.now().strftime("%H:%M:%S")} - Import OK")

    @Slot(QNetworkReply)
    def handle_online_res_reply(self, reply: QNetworkReply):
        self.log.append(
            f"{datetime.now().strftime("%H:%M:%S")} - Online výsledky: {"OK" if reply.error() == QNetworkReply.NetworkError.NoError else f"ERROR: {reply.error().name}"} {reply.readAll().data().decode("utf-8")}"
        )

    def _send_online_readout(self, db, si: int, all: bool = False):
        sess = Session(db)

        if not api.get_basic_info(db)["robis_api"]:
            return

        categories = []
        if not all:
            runner = sess.scalars(Select(Runner).where(Runner.si == si)).one()
            categories = [runner.category]
        else:
            runner = None
            categories = sess.scalars(Select(Category)).all()

        for category in categories:
            data = []
            results_cat = results.calculate_category(db, category.name)

            for result in results_cat:
                if runner and runner.reg != result.reg:
                    continue
                order = []
                last = result.start
                for punch in result.order:
                    order.append(
                        {
                            "code": punch[0],
                            "control_type": "CONTROL" if punch[0] != "M" else "BEACON",
                            "punch_status": punch[2],
                            "split_time": results.format_delta(punch[1] - last),
                        }
                    )
                    last = punch[1]
                if result.finish:
                    order.append(
                        {
                            "code": "F",
                            "control_type": "FINISH",
                            "punch_status": "OK",
                            "split_time": results.format_delta(result.finish - last),
                        }
                    )

                data.append(
                    {
                        "competitor_index": result.reg,
                        "si_number": result.si,
                        "last_name": result.name.split(", ")[0],
                        "first_name": result.name.split(", ")[1],
                        "category_name": category.name,
                        "result": {
                            "run_time": results.format_delta(
                                timedelta(seconds=result.time)
                            ),
                            "controls_num": result.tx,
                            "result_status": result.status,
                            "punches": order,
                        },
                    }
                )

            sess.close()

            json_data = json.dumps(data)
            byte_data = QByteArray(json_data.encode("utf-8"))

            request = QNetworkRequest(QUrl("https://rob-is.cz/api/results/?name=json"))

            request.setHeader(
                QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json"
            )
            request.setRawHeader(
                QByteArray("Race-Api-Key"),
                QByteArray(api.get_basic_info(db)["robis_api"]),
            )

            self.nmmanager.put(request, byte_data)
