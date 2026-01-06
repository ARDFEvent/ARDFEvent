import time
from datetime import datetime, timedelta

from PySide6.QtCore import QThread, Signal, QCoreApplication
from PySide6.QtCore import QUrl
from PySide6.QtGui import QCloseEvent, Qt
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QCompleter,
    QDialog,
    QFormLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget, QHBoxLayout, QRadioButton, QSpinBox, QFrame, QFileDialog,
)
from escpos.escpos import Escpos
from escpos.printer import Usb, Serial, Dummy
from serial.tools.list_ports import comports
from sportident import SIReaderReadout
from sqlalchemy import Delete, Select
from sqlalchemy.orm import Session

import api
import results
from models import Control, Punch, Runner
from results import format_delta
from ui.qtaiconbutton import QTAIconButton


class ReadoutThread(QThread):
    def __init__(self, parent, si_port) -> None:
        super().__init__(parent)
        self.si_port = si_port

    def run(self) -> None:
        try:
            si = SIReaderReadout(self.si_port)

            si.beep(3)

            while True:
                while not si.poll_sicard():
                    time.sleep(0.01)

                try:
                    data = si.read_sicard()
                    si.ack_sicard()
                    self.parent().on_readout.emit(data)

                except Exception as e:
                    if str(e) != "No card in the device.":
                        si.beep(2)
                        self.parent().si_error.emit()
        except Exception as e:
            self.parent().thr_err.emit(e.__str__())


class ReadoutWindow(QWidget):
    on_readout = Signal(dict)
    si_error = Signal()
    thr_err = Signal(str)

    def __init__(self, mw):
        super().__init__()

        self.printer: Escpos | None = None
        self.printer_optns: PrinterOptions | None = None

        self.mw = mw
        self.state_win = ReadoutStatusWindow(mw)
        self.printer_win = PrinterSetupDialog(self)

        self.proc: ReadoutThread = None

        self.snura_i = 0

        self.on_readout.connect(self._handle_readout)
        self.si_error.connect(self._show_si_error)
        self.thr_err.connect(self._proc_stopped)

        lay = QVBoxLayout()
        self.setLayout(lay)

        portslay = QHBoxLayout()
        lay.addLayout(portslay)

        portslay.addWidget(QLabel("SI:"))

        self.siport_edit = QComboBox()
        portslay.addWidget(self.siport_edit)

        printerconfigure_btn = QTAIconButton("mdi6.printer-pos-wrench-outline",
                                             QCoreApplication.translate("ReadoutWindow", "Konfigurovat tiskárnu"))
        printerconfigure_btn.clicked.connect(self.printer_win.exec)
        portslay.addWidget(printerconfigure_btn)

        self.double_print_chk = QTAIconButton("mdi6.receipt-text-plus-outline",
                                              QCoreApplication.translate("ReadoutWindow", "Dvojtisk"))
        self.double_print_chk.setCheckable(True)
        portslay.addWidget(self.double_print_chk)

        portslay.addStretch()

        self.state_label = QLabel(QCoreApplication.translate("ReadoutWindow", "Stav: Neaktivní"))
        portslay.addWidget(self.state_label)
        self.state_label.setStyleSheet("color: red;")

        startreadout_btn = QTAIconButton("mdi6.power", QCoreApplication.translate("ReadoutWindow", "Spustit/vypnout"))
        startreadout_btn.clicked.connect(self._toggle_readout)
        portslay.addWidget(startreadout_btn)

        self.log = QTextBrowser()
        lay.addWidget(self.log)

    def _show_si_error(self):
        self.state_win.set_error(QCoreApplication.translate("ReadoutWindow", "CHYBA SI"))
        QMessageBox.critical(self, QCoreApplication.translate("ReadoutWindow", "Chyba"),
                             QCoreApplication.translate("ReadoutWindow", "Zkuste to znovu"))
        self.state_win.set_error(None)

    def _toggle_readout(self):
        if self.proc:
            self.proc.terminate()
            self.proc.wait()
            self.proc = None
            self.state_win.stop()
            if self.printer:
                self.printer.close()

        else:
            self.proc = ReadoutThread(self, self.siport_edit.currentText())
            self.proc.started.connect(self._proc_running)
            self.proc.finished.connect(self._proc_stopped)
            self.proc.start()

            self.state_win.show()
            self.state_win.set_ports(self.siport_edit.currentText())

    def _proc_running(self):
        self.state_label.setText(QCoreApplication.translate("ReadoutWindow", "Stav: Aktivní"))
        self.state_label.setStyleSheet("color: green;")

    def _proc_stopped(self, msg=None):
        self.state_label.setText(QCoreApplication.translate("ReadoutWindow", "Stav: Neaktivní"))
        self.state_label.setStyleSheet("color: red;")
        self.log.setText(
            self.log.toPlainText() + msg + "\n" if msg else QCoreApplication.translate("ReadoutWindow",
                                                                                       "Čtení ukončeno.\n")
        )
        self.state_win.close()

    def _append_log(self, string: str):
        self.log.setText(self.log.toPlainText() + string + "\n")

    def _handle_readout(self, data):
        si_no = data["card_number"]

        self._append_log("---------------------------------")
        self._append_log(QCoreApplication.translate("ReadoutWindow", "Byl vyčten čip %d.") % si_no)

        with Session(self.mw.db) as sess:
            runners = sess.scalars(Select(Runner).where(Runner.si == si_no)).all()

            if len(sess.scalars(Select(Punch).where(Punch.si == si_no)).all()) != 0:
                self.state_win.set_error(QCoreApplication.translate("ReadoutWindow", "JIŽ VYČTENÝ ČIP"))
                if (
                        QMessageBox.warning(
                            self,
                            QCoreApplication.translate("ReadoutWindow", "Chyba"),
                            QCoreApplication.translate("ReadoutWindow", "Čip %d byl již vyčten. Přepsat?") % si_no,
                            QMessageBox.StandardButton.Yes,
                            QMessageBox.StandardButton.No,
                        )
                        == QMessageBox.StandardButton.Yes
                ):
                    self._append_log(QCoreApplication.translate("ReadoutWindow", "Přepsán předchozí zápis."))
                    sess.execute(Delete(Punch).where(Punch.si == si_no))
                    self.state_win.set_error(None)
                else:
                    self._append_log(QCoreApplication.translate("ReadoutWindow", "Zrušeno vyčtení."))
                    self.state_win.set_error(None)
                    return

            for punch in data["punches"]:
                sess.add(Punch(si=si_no, code=punch[0], time=punch[1].replace(microsecond=0)))

            if data["start"]:
                sess.add(Punch(si=si_no, code=1000, time=data["start"].replace(microsecond=0)))

            if data["finish"]:
                sess.add(Punch(si=si_no, code=1001, time=data["finish"].replace(microsecond=0)))

            if len(runners) == 0:
                self.state_win.set_error(QCoreApplication.translate("ReadoutWindow", "NENALEZEN ČIP"))
                all_runners = map(lambda x: x.name if not x.startno else f"{x.startno}, {x.name}",
                                  sess.scalars(Select(Runner)).all())

                inpd = QInputDialog()
                inpd.setWindowTitle(QCoreApplication.translate("ReadoutWindow", "Nepřiřazený čip"))
                inpd.setLabelText(
                    QCoreApplication.translate("ReadoutWindow", "Čip není přiřazen. Zadejte jméno nebo st. číslo."))
                inpd.setTextValue("")
                completer = QCompleter(all_runners, inpd)
                completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                label: QLineEdit = inpd.findChild(QLineEdit)
                label.setCompleter(completer)

                ok, name = (
                    inpd.exec() == QDialog.Accepted,
                    inpd.textValue(),
                )
                self.state_win.set_error(None)

                if ok:
                    try:
                        runner = sess.scalars(
                            Select(Runner).where(Runner.name == name)
                        ).one()
                        runner.si = si_no
                    except:
                        self._append_log(QCoreApplication.translate("ReadoutWindow",
                                                                    "Nenalezeno. Čip je v DB, není ale přiřazen závodníkovi."))
                        return
                else:
                    self._append_log(
                        QCoreApplication.translate("ReadoutWindow", "Čip je v DB, není ale přiřazen závodníkovi."))
                    return
            else:
                runner = runners[0]

            sess.scalars(Select(Runner).where(Runner.si == si_no)).one().manual_dns = False

            self._append_log(
                QCoreApplication.translate("ReadoutWindow", "Závodník: %s (%s).") % (runner.name, runner.reg))
            self.state_win.set_runner(
                f"{runner.name} ({runner.reg}), {runner.category.name}"
            )

            sess.commit()

        if self.printer:
            self.print_readout(si_no)
            if self.double_print_chk.isChecked() and (
                    self.printer_optns.cut or QMessageBox.warning(self, QCoreApplication.translate("ReadoutWindow",
                                                                                                   "Dvojtisk"),
                                                                  QCoreApplication.translate("ReadoutWindow",
                                                                                             "Tisknout podruhé?"),
                                                                  QMessageBox.StandardButton.Ok,
                                                                  QMessageBox.StandardButton.Abort, ) == QMessageBox.StandardButton.Ok):
                self.print_readout(si_no, True)

        self.mw.results_win._update_results()
        self.mw.inforest_win._update()
        self.mw.pl.readout(si_no)

    def _update_ports(self):
        oldportsi = self.siport_edit.currentText()

        self.siport_edit.clear()

        for port in comports()[::-1]:
            self.siport_edit.addItem(port.device)

        if self.proc is not None:
            idx_si = self.siport_edit.findData(oldportsi)
            if idx_si != -1:
                self.siport_edit.setCurrentIndex(idx_si)

    def _show(self):
        self._update_ports()

    def closeEvent(self, event: QCloseEvent) -> None:
        try:
            self.proc.terminate()
            self.proc.wait()
            self.state_win.stop()
        except:
            ...
        super().closeEvent(event)

    def print_readout(self, si: int, snura=False):
        def text(string: str = ""):
            self.printer._raw(string.encode("cp852"))

        def line(string: str = ""):
            text(string + "\n")

        with Session(self.mw.db) as sess:
            runner = sess.scalars(Select(Runner).where(Runner.si == si)).one()
            basic_info = api.get_basic_info(self.mw.db)
            results_cat = results.calculate_category(self.mw.db, runner.category.name)
            try:
                result = list(filter(lambda x: x.name == runner.name, results_cat))[0]
            except:
                return

            if not snura:
                if self.printer_optns.logo:
                    self.printer.set(align="center", double_height=False)
                    self.printer.image(self.printer_optns.logo)

                if self.printer_optns.title:
                    self.printer.set(align="center", double_height=True)
                    line(basic_info["name"])
                    self.printer.set(align="center", double_height=False)
                    line(datetime.fromisoformat(basic_info["date_tzero"]).strftime("%d. %m. %Y"))
                self.printer.set(align="left")
                line()
            else:
                self.snura_i += 1
                line(runner.category.name)
                line(f"LÍSTEK Č. {self.snura_i}, {datetime.now().strftime("%H:%M:%S")}")
                if result.status == "OK":
                    line(f"{result.place}. MÍSTO")
                else:
                    line("NA KONEC - není OK")
                line("\n")

            punches = list(sess.scalars(Select(Punch).where(Punch.si == si)).all())
            punches.sort(key=lambda x: x.time)

            start = sess.scalars(
                Select(Punch).where(Punch.si == si).where(Punch.code == 1000)
            ).one_or_none()

            if not snura:
                self.printer.set(bold=True)
                text(runner.name)
                self.printer.set(bold=False)
                text(f" ({runner.reg}), ")
                self.printer.set(bold=True)
                line(runner.category.name)
                self.printer.set(bold=False)
                line(f"Klub:  {runner.club}")
                line(f"SI:    {runner.si}")
            else:
                self.printer.set(align="center", double_height=True)
                line(runner.name)
                self.printer.set(align="left", double_height=False)
                line(f"{runner.reg}, {runner.category.name}")

            startovka = None

            if runner.startlist_time:
                startovka = runner.startlist_time
                line(f"Start: {startovka.strftime('%H:%M:%S')}")

            line("")

            if start:
                stime: datetime = start.time
            elif startovka:
                stime: datetime = startovka
            else:
                stime: datetime = datetime.fromisoformat(api.get_basic_info(self.mw.db)["date_tzero"])

            lasttime = stime

            self.printer.set(bold=True)
            line(f"Kód\tČas\tMezičas{"\t Reálný čas" if self.printer_optns.paper else ""}".expandtabs(10))
            self.printer.set(bold=False)

            for punch in punches:
                controls = sess.scalars(
                    Select(Control).where(Control.code == punch.code)
                ).all()

                for icontrol in controls:
                    if icontrol in runner.category.controls:
                        control = icontrol
                        break
                else:
                    control = controls[0] if len(controls) else None

                if control:
                    cn_name = f"({punch.code}) {control.name if control in runner.category.controls else f'{control.name}+'}"
                elif punch.code == 1000:
                    cn_name = "Start"
                elif punch.code == 1001:
                    cn_name = "Finish"
                else:
                    cn_name = f"({punch.code}) N/A"
                ptime: datetime = punch.time
                fromstart = ptime - stime
                split = ptime - lasttime

                line(
                    f"{cn_name}\t{format_delta(fromstart)}\t+{format_delta(split)}{f"\t {ptime.strftime("%H:%M:%S")}" if self.printer_optns.paper else ""}".expandtabs(
                        10
                    )
                )

                lasttime = ptime

            line()

            text("Výsledek: ")
            self.printer.set(bold=True)
            line(
                f"{format_delta(timedelta(seconds=result.time))}, {result.tx} TX, {result.status}\n"
            )
            self.printer.set(bold=False)
            if not snura:
                self.printer.set(bold=True)
                line("Výsledky:")
                self.printer.set(bold=False)

                for result_lp in results_cat[:3]:
                    if result_lp.status != "OK":
                        continue
                    place = f"{result_lp.place}."
                    self.printer.set(align="left")
                    text(f"{place} {result_lp.name}{" " if self.printer_optns.paper else "\n"}")
                    if not self.printer_optns.paper:
                        self.printer.set(align="right")
                    line(
                        f"{"(" if self.printer_optns.paper else ""}{format_delta(timedelta(seconds=result_lp.time))}, {result_lp.tx} TX{")" if self.printer_optns.paper else ""}"
                    )

                if result.place > 3 or result.status != "OK":
                    self.printer.set(bold=True)
                    place = f"{result.place}."
                    self.printer.set(align="left")
                    text(f"{place} {result.name}{" " if self.printer_optns.paper else "\n"}")
                    if not self.printer_optns.paper:
                        self.printer.set(align="right")
                    line(
                        f"{"(" if self.printer_optns.paper else ""}{format_delta(timedelta(seconds=result.time))}, {result.tx} TX{")" if self.printer_optns.paper else ""}"
                    )

                if self.printer_optns.qr or self.printer_optns.link:
                    self.printer.set(align="left", bold=True)
                    line("\nŽivé výsledky:" + (" rob-is.cz/vysledky" if self.printer_optns.link else ""))
                    if self.printer_optns.qr:
                        self.printer.set(align="center")
                        self.printer.qr("https://rob-is.cz/vysledky", size=5)
                    else:
                        line()
                else:
                    line()
            else:
                line()

            self.printer.set(align="center")
            line("JJ ARDFEvent, (C) Jakub Jiroutek")

            if self.printer_optns.cut:
                self.printer.cut()
            self.printer.print_and_feed(self.printer_optns.feed)

            if isinstance(self.printer, Dummy):
                print("-" * 50)
                try:
                    print(self.printer.output.decode("CP852"))
                except:
                    print(self.printer.output)
                self.printer.clear()


class PrinterOptions:
    def __init__(self, paper, title, feed, cut, logo, link, qr):
        self.paper: bool = paper
        self.title: bool = title
        self.feed: int = feed
        self.cut: bool = cut
        self.logo: str = logo
        self.link: bool = link
        self.qr: bool = qr


class PrinterSetupDialog(QDialog):
    def __init__(self, parent: ReadoutWindow):
        super().__init__(parent)

        self.rdowin = parent

        self.setWindowTitle("Nastavení účtenkové tiskárny")

        main_lay = QVBoxLayout()
        self.setLayout(main_lay)

        preset_lay = QHBoxLayout()
        main_lay.addLayout(preset_lay)

        preset_lay.addWidget(QLabel("Přednastavení:"))

        epson_btn = QPushButton("Epson TM-T20III (USB)")
        epson_btn.clicked.connect(self._epson_preset)
        preset_lay.addWidget(epson_btn)

        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)

        main_lay.addWidget(line2)

        self.noprint_optn = QRadioButton("Netisknout")
        self.noprint_optn.setChecked(True)
        self.noprint_optn.clicked.connect(self._toggle)
        main_lay.addWidget(self.noprint_optn)

        self.serial_optn = QRadioButton("Sériový port (COMX, /dev/ttySX nebo /dev/ttyUSBX)")
        self.serial_optn.clicked.connect(self._toggle)
        main_lay.addWidget(self.serial_optn)
        self.serial_edit = QComboBox()
        main_lay.addWidget(self.serial_edit)

        self.usb_optn = QRadioButton("USB (nativní)")
        self.usb_optn.clicked.connect(self._toggle)
        main_lay.addWidget(self.usb_optn)
        usb_lay = QFormLayout()
        main_lay.addLayout(usb_lay)
        self.usbvendor_edit = QLineEdit()
        self.usbvendor_edit.setInputMask("HHHH")
        usb_lay.addRow("USB výrobce (HEX)", self.usbvendor_edit)
        self.usbmodel_edit = QLineEdit()
        self.usbmodel_edit.setInputMask("HHHH")
        usb_lay.addRow("USB model (HEX)", self.usbmodel_edit)

        self.dummy_optn = QRadioButton("Dummy - pouze testovací")
        self.dummy_optn.clicked.connect(self._toggle)
        main_lay.addWidget(self.dummy_optn)

        line1 = QFrame()
        line1.setFrameShape(QFrame.Shape.HLine)
        line1.setFrameShadow(QFrame.Shadow.Sunken)

        main_lay.addWidget(line1)

        set_lay = QFormLayout()
        main_lay.addLayout(set_lay)

        self.paper_edit = QComboBox()
        self.paper_edit.addItems(["58 mm", "80 mm"])
        set_lay.addRow("Šířka papíru", self.paper_edit)

        self.feed_edit = QSpinBox()
        self.feed_edit.setMinimum(0)
        self.feed_edit.setMaximum(99)
        set_lay.addRow("Feed na konci", self.feed_edit)

        self.logo_lbl = QLabel()
        logo_btn = QPushButton("Vybrat soubor...")
        logo_btn.clicked.connect(self._logo_select)
        set_lay.addRow("Logo do záhlaví", self.logo_lbl)
        set_lay.addWidget(logo_btn)

        self.title_check = QCheckBox("Tisknout název závodu")
        self.title_check.setChecked(True)
        main_lay.addWidget(self.title_check)

        self.cut_check = QCheckBox("Řezat lístky (jen když to tiskárna umí)")
        main_lay.addWidget(self.cut_check)

        self.link_check = QCheckBox("Tisknout odkaz na živé výsledky na ROBis")
        main_lay.addWidget(self.link_check)

        self.qr_check = QCheckBox("Tisknout QR kód na živé výsledky na ROBis")
        main_lay.addWidget(self.qr_check)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self._ok)
        main_lay.addWidget(ok_btn)

        self._toggle()

    def _logo_select(self):
        file, ok = QFileDialog.getOpenFileName(self, "Vybrat logo", filter="Obrázek (*.jpg, *.png)")
        if ok:
            self.logo_lbl.setText(file)

    def _ok(self):
        if self.rdowin.printer:
            self.rdowin.printer.close()

        if self.noprint_optn.isChecked():
            self.rdowin.printer = None
            self.close()
            return
        elif self.serial_optn.isChecked():
            self.rdowin.printer = Serial(self.serial_edit.currentText())
        elif self.usb_optn.isChecked():
            self.rdowin.printer = Usb(int(self.usbvendor_edit.text(), 16), int(self.usbmodel_edit.text(), 16))
        elif self.dummy_optn.isChecked():
            self.rdowin.printer = Dummy()

        self.rdowin.printer.charcode("CP852")

        self.rdowin.printer_optns = PrinterOptions(self.paper_edit.currentText() == "80 mm",
                                                   self.title_check.isChecked(), self.feed_edit.value(),
                                                   self.cut_check.isChecked(), self.logo_lbl.text(),
                                                   self.link_check.isChecked(), self.qr_check.isChecked())
        self.close()

    def _epson_preset(self):
        self.usb_optn.setChecked(True)
        self._toggle()
        self.usbvendor_edit.setText("04b8")
        self.usbmodel_edit.setText("0e28")
        self.paper_edit.setCurrentIndex(1)
        self.feed_edit.setValue(1)
        self.cut_check.setChecked(True)

    def exec(self):
        self.serial_edit.clear()
        self.serial_edit.addItems([p.device for p in comports()[::-1]])
        super().exec()

    def _toggle(self):
        self.serial_edit.setEnabled(self.serial_optn.isChecked())
        self.usbvendor_edit.setEnabled(self.usb_optn.isChecked())
        self.usbmodel_edit.setEnabled(self.usb_optn.isChecked())


class InForestThread(QThread):
    def __init__(self, parent):
        super().__init__(parent)

    def run(self):
        self.parent().runners.emit()
        time.sleep(30.0 - (time.time() % 30.0))
        while True:
            self.parent().runners.emit()
            time.sleep(1)


class ReadoutStatusWindow(QWidget):
    runners = Signal()

    def __init__(self, mw):
        super().__init__()
        self.setWindowTitle("JJ ARDFEvent - Stav vyčítání")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.mw = mw

        self.upd_thr = None

        layout = QVBoxLayout()
        self.setLayout(layout)

        self.mainstate_label = QLabel()
        layout.addWidget(self.mainstate_label)

        last_label = QLabel("\nNaposledy vyčtený závodník:")
        last_label.setStyleSheet("QLabel { font-weight: bold; }")
        layout.addWidget(last_label)

        self.runner_label = QLabel("Nic nevyčteno :(")
        layout.addWidget(self.runner_label)

        self.time_label = QLabel()
        layout.addWidget(self.time_label)

        self.error_label = QLabel()
        layout.addWidget(self.error_label)

        people_layout = QHBoxLayout()
        layout.addLayout(people_layout)

        self.inforest_label = QLabel("0")
        self.inforest_label.setStyleSheet(
            "QLabel { background-color: red; color: white; padding: 5px; font-size: 50px; }")
        self.inforest_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        people_layout.addWidget(self.inforest_label)

        self.finished_label = QLabel("0")
        self.finished_label.setStyleSheet(
            "QLabel { background-color: green; color: white; padding: 5px; font-size: 50px; }")
        self.finished_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        people_layout.addWidget(self.finished_label)

        self.not_started = QLabel("0")
        self.not_started.setStyleSheet(
            "QLabel { background-color: yellow; color: black; padding: 5px; font-size: 50px; }")
        self.not_started.setAlignment(Qt.AlignmentFlag.AlignCenter)
        people_layout.addWidget(self.not_started)

        self.effect = QSoundEffect()
        self.effect.setSource(QUrl.fromLocalFile(":/sound/error.wav"))
        self.effect.setLoopCount(-2)
        self.effect.setVolume(1.0)

        self.runners.connect(self._set_counts)

        self.set_error(None)

    def show(self):
        super().show()
        self.upd_thr = InForestThread(self)
        self.upd_thr.start()

    def stop(self):
        self.upd_thr.terminate()
        self.upd_thr = None

    def _set_counts(self):
        with Session(self.mw.db) as sess:
            now = datetime.now()
            in_forest = sess.scalars(
                Select(Runner)
                .where(~Runner.manual_dns)
                .where(~Runner.manual_disk)
                .where(Runner.si.not_in(Select(Punch.si)))
                .where(Runner.startlist_time < now)
            ).all()

            finished = sess.scalars(
                Select(Runner)
                .where(~Runner.manual_dns)
                .where(~Runner.manual_disk)
                .where(Runner.si.in_(Select(Punch.si)))
            ).all()

            not_started_yet = sess.scalars(
                Select(Runner)
                .where(~Runner.manual_dns)
                .where(~Runner.manual_disk)
                .where(Runner.startlist_time > now)
            ).all()

            self.inforest_label.setText(f"{len(in_forest)}")
            self.finished_label.setText(f"{len(finished)}")
            self.not_started.setText(f"{len(not_started_yet)}")

    def set_ports(self, si: str):
        self.mainstate_label.setText(f"Stav: Aktivní, SI: {si}")
        self.mainstate_label.setStyleSheet("color: green;")

    def set_runner(self, runner: str):
        self.runner_label.setText(runner)
        self.time_label.setText(f"Vyčten v: {datetime.now().strftime("%H:%M:%S")}")
        self._set_counts()

    def set_error(self, error: str | None):
        if error:
            self.error_label.setText(error)
            self.error_label.setStyleSheet(
                "color: red; font-weight: bold; font-size: 64px;"
            )
            self.effect.play()
        else:
            self.error_label.setText("OK")
            self.error_label.setStyleSheet(
                "color: green; font-weight: bold; font-size: 64px;"
            )
            self.effect.stop()
