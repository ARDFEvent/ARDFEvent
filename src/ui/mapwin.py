import itertools
import json
import os
import tempfile
from enum import Enum

from PySide6.QtCore import QUrl, QObject, Slot, Qt, Signal, Property
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtWidgets import QVBoxLayout, QWidget, QPushButton, QFileDialog, QHBoxLayout, QInputDialog, QLineEdit, \
    QLabel, QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QFormLayout, \
    QSpinBox
from osgeo import gdal
from sqlalchemy import Select, or_
from sqlalchemy.orm import Session

import api
import ardfevent_rust.routes as r_routes
import routes
from models import Control, Category
from ui.qtaiconbutton import QTAIconButton


class MapWindowClickModes(Enum):
    NONE = 0
    ADD_CONTROL = 1
    ADD_START = 2
    ADD_FINISH = 3


class GeoMapper(QObject):
    def __init__(self, file_path, srs):
        super().__init__()

        temp_dir = tempfile.gettempdir()
        self._imagePath = os.path.join(temp_dir, "tmpmapa.png")

        self._lat = 0.0
        self._lon = 0.0
        self._w_deg = 0.0
        self._h_deg = 0.0

        resolved_input = file_path if os.path.isabs(file_path) else os.path.join(os.path.dirname(__file__), file_path)

        try:
            gdal.Warp(self._imagePath, resolved_input,
                      srcSRS=srs,
                      dstSRS=f"EPSG:3857",
                      format="PNG")
            ds_4326 = gdal.Warp("", resolved_input, format="VRT",
                                srcSRS="EPSG:5514", dstSRS="EPSG:4326")
        except Exception as e:
            return

        gt = ds_4326.GetGeoTransform()
        if gt is None:
            return

        self._lat = gt[3]
        self._lon = gt[0]

        self._w_deg = ds_4326.RasterXSize * gt[1]
        self._h_deg = abs(ds_4326.RasterYSize * gt[5])

        try:
            ds_3857 = gdal.Open(self._imagePath)
            gt_3857 = ds_3857.GetGeoTransform()
            self._w_meters = ds_3857.RasterXSize * gt_3857[1]
            self._h_meters = abs(ds_3857.RasterYSize * gt_3857[5])
        except Exception as e:
            self._w_meters = 0.0
            self._h_meters = 0.0

    def asdict(self):
        return {
            "topLeftLat": self._lat,
            "topLeftLon": self._lon,
            "widthDeg": self._w_deg,
            "heightDeg": self._h_deg,
            "widthMeters": self._w_meters,
            "heightMeters": self._h_meters,
            "imagePath": self._imagePath,
        }


class MapHandler(QObject):
    controlsChange = Signal(str)
    addPath = Signal(str)
    circlesChanged = Signal()
    removePaths = Signal()

    def __init__(self, map_win):
        super().__init__()
        self.mw = map_win.mw

        map_win.settings_win.start_edit.editingFinished.connect(self.circlesChanged)
        map_win.settings_win.control_edit.editingFinished.connect(self.circlesChanged)

    @Slot(str, float, float)
    def control_moved(self, cid_str, lat, lon):
        if cid_str.startswith("START-") or cid_str.startswith("FINISH-"):
            starts_finishes = api.get_starts_finishes(self.mw.db)
            idx = int(cid_str.split("-")[1])
            if cid_str.startswith("START-"):
                if idx < len(starts_finishes.get("starts", [])):
                    starts_finishes["starts"][idx] = {"lat": lat, "lon": lon}
            else:
                if idx < len(starts_finishes.get("finishes", [])):
                    starts_finishes["finishes"][idx] = {"lat": lat, "lon": lon}
            api.set_basic_info(self.mw.db, {"map_starts_finishes": json.dumps(starts_finishes)})
            self.update_map_items()
            return
        with Session(self.mw.db) as session:
            control = session.scalars(Select(Control).where(Control.id == int(cid_str))).one_or_none()
            if control:
                control.lat = lat
                control.lon = lon
                session.commit()
        self.mw.map_win.change_category()

    @Slot(str)
    def control_dblclicked(self, cid_str):
        if cid_str.startswith("START-") or cid_str.startswith("FINISH-"):
            starts_finishes = api.get_starts_finishes(self.mw.db)
            cat = self.mw.map_win.selected_category
            idx = int(cid_str.split("-")[1])
            if not cat in starts_finishes["categories"]:
                starts_finishes["categories"][cat] = {"start": None, "finish": None}
            if cid_str.startswith("START-"):
                if idx < len(starts_finishes.get("starts", [])):
                    starts_finishes["categories"][cat]["start"] = idx
            else:
                if idx < len(starts_finishes.get("finishes", [])):
                    starts_finishes["categories"][cat]["finish"] = idx
            api.set_basic_info(self.mw.db, {"map_starts_finishes": json.dumps(starts_finishes)})
        else:
            with Session(self.mw.db) as session:
                control = session.scalars(Select(Control).where(Control.id == int(cid_str))).one_or_none()
                category = session.scalars(
                    Select(Category).where(Category.name == self.mw.map_win.selected_category)).one_or_none()
                if control and category:
                    if control in category.controls:
                        category.controls.remove(control)
                    else:
                        category.controls.append(control)
                    category.controls = api.sort_controls(category.controls)
                    session.commit()

        self.update_map_items()
        self.mw.map_win.change_category()

    @Slot(float, float)
    def handle_click(self, lat, lon):
        if self.mw.map_win.mode == MapWindowClickModes.NONE:
            return
        elif self.mw.map_win.mode == MapWindowClickModes.ADD_CONTROL:
            self.mw.map_win.mode = MapWindowClickModes.NONE
            if res := self.mw.map_win.new_control_win.result:
                with Session(self.mw.db) as sess:
                    control = sess.scalars(
                        Select(Control).where(Control.id == res)).one_or_none()
                    if control:
                        control.lat = lat
                        control.lon = lon
                        sess.commit()
        elif (
                start := self.mw.map_win.mode == MapWindowClickModes.ADD_START) or self.mw.map_win.mode == MapWindowClickModes.ADD_FINISH:
            self.mw.map_win.mode = MapWindowClickModes.NONE
            starts_finishes = api.get_starts_finishes(self.mw.db)
            starts_finishes["starts" if start else "finishes"].append({"lat": lat, "lon": lon})
            api.set_basic_info(self.mw.db, {"map_starts_finishes": json.dumps(starts_finishes)})
        self.update_map_items()

    def update_map_items(self, center=False):
        starts_finishes = json.loads(api.get_basic_info(self.mw.db).get("map_starts_finishes", "{}"))
        with Session(self.mw.db) as session:
            controls = session.scalars(Select(Control)).all()
            category = session.scalars(
                Select(Category).where(Category.name == self.mw.map_win.selected_category)).one()

            points = []
            for control in controls:
                if not control.lat or not control.lon:
                    continue
                points.append(
                    {"control_id": str(control.id), "type": "control", "latitude": control.lat,
                     "longitude": control.lon,
                     "label": control.name, "active": control in category.controls})
            for i, start in enumerate(starts_finishes["starts"]):
                if not start.get("lat") or not start.get("lon"):
                    continue
                points.append(
                    {"control_id": f"START-{i}", "type": "start", "latitude": start.get("lat"),
                     "longitude": start.get("lon"), "label": f"S{i + 1}",
                     "active": starts_finishes["categories"].get(self.mw.map_win.selected_category, {}).get(
                         "start") == i})
            for j, finish in enumerate(starts_finishes["finishes"]):
                if not finish.get("lat") or not finish.get("lon"):
                    continue
                points.append(
                    {"control_id": f"FINISH-{j}", "type": "finish", "latitude": finish.get("lat"),
                     "longitude": finish.get("lon"), "label": f"F{j + 1}",
                     "active": starts_finishes["categories"].get(self.mw.map_win.selected_category, {}).get(
                         "finish") == j})
            self.controlsChange.emit(json.dumps({"center": center, "arr": points}))

        self.removePaths.emit()

        res = routes.calculate_category_route(self.mw.db, self.mw.map_win.selected_category)
        if res:
            points, length = res
            last = points[0]
            for point in points[1:]:
                self.addPath.emit(
                    json.dumps([{"lat": last.lat, "lon": last.lon}, {"lat": point.lat, "lon": point.lon}]))
                last = point
            return length
        return 0

    @Property(int, notify=circlesChanged)
    def start_circle(self):
        return self.mw.map_win.settings_win.start_edit.value()

    @Property(int, notify=circlesChanged)
    def control_circle(self):
        return self.mw.map_win.settings_win.control_edit.value()


class NewControlWindow(QWidget):
    def __init__(self, mw):
        super().__init__()
        self.mw = mw
        self.result = None

        lay = QVBoxLayout()
        self.setLayout(lay)

        lay.addWidget(QLabel("Založit novou kontrolu:"))
        self.newname_edit = QLineEdit()
        self.newname_edit.setPlaceholderText("Název kontroly")
        lay.addWidget(self.newname_edit)

        lay.addWidget(QLabel("Nezapomeňte před závodem doplnit SI kód!"))

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self._ok)
        lay.addWidget(ok_btn)

        lay.addWidget(QLabel("Umístit existující kontrolu (dvojklik):"))

        self.avail_list = QListWidget()
        self.avail_list.itemDoubleClicked.connect(self._selected_control)
        lay.addWidget(self.avail_list)

    def show(self):
        super().show()
        self.result = None
        with Session(self.mw.db) as session:
            controls = session.scalars(Select(Control).where(or_(Control.lat == None, Control.lon == None))).all()
            self.avail_list.clear()
            for control in controls:
                item = QListWidgetItem(control.name)
                item.setData(Qt.UserRole, control.id)
                self.avail_list.addItem(item)

    def _selected_control(self, item: QListWidgetItem):
        cid = item.data(Qt.UserRole)
        if not cid:
            return
        with Session(self.mw.db) as session:
            control = session.scalars(Select(Control).where(Control.id == cid)).one_or_none()
            if control:
                self.result = control.id
        self.close()
        self.mw.map_win.mode = MapWindowClickModes.ADD_CONTROL

    def _ok(self):
        name = self.newname_edit.text()
        with Session(self.mw.db) as session:
            control = Control(name=name, code=-1, mandatory=False, spectator=False, lat=None, lon=None)
            session.add(control)
            session.commit()
            self.result = control.id
        self.close()
        self.mw.map_win.mode = MapWindowClickModes.ADD_CONTROL


class CSSettingsWindow(QWidget):
    PRESETS = [("CZ klasika", 750, 400), ("CZ krátká", 500, 400), ("CZ sprint", 100, 100),
               ("CZ foxoring", 250, 250)]

    def __init__(self, mw):
        super().__init__()
        self.mw = mw

        self.setWindowTitle("Nastavení stavby tratí")

        lay = QFormLayout()
        self.setLayout(lay)

        for preset in self.PRESETS:
            btn = QPushButton(preset[0])
            btn.clicked.connect(lambda checked, p=preset: self._preset_clicked(p))
            lay.addRow(btn)

        self.start_edit = QSpinBox()
        self.start_edit.setRange(0, 10000)
        self.start_edit.setValue(750)
        lay.addRow("Startovní kolečko:", self.start_edit)

        self.control_edit = QSpinBox()
        self.control_edit.setRange(0, 10000)
        self.control_edit.setValue(400)
        lay.addRow("Kolečko okolo kontrol:", self.control_edit)

    def _preset_clicked(self, preset):
        self.start_edit.setValue(preset[1])
        self.control_edit.setValue(preset[2])
        self.start_edit.editingFinished.emit()


class MapWindow(QWidget):
    def __init__(self, mw):
        super().__init__()
        self.mw = mw
        self.mode = MapWindowClickModes.NONE
        self.selected_category = None

        self.new_control_win = NewControlWindow(self.mw)
        self.settings_win = CSSettingsWindow(self.mw)

        layout = QHBoxLayout()
        self.setLayout(layout)

        maplayout = QVBoxLayout()
        layout.addLayout(maplayout, stretch=1)

        toolbar = QHBoxLayout()
        maplayout.addLayout(toolbar)

        self.open_btn = QPushButton("Otevřít mapu")
        self.open_btn.clicked.connect(self.open_map)
        toolbar.addWidget(self.open_btn)

        self.settings_btn = QPushButton("Nastavení stavby tratí")
        self.settings_btn.clicked.connect(self.settings_win.show)
        toolbar.addWidget(self.settings_btn)

        toolbar.addStretch()

        toolbar.addWidget(QLabel("Přidat:"))

        self.addctrl_btn = QTAIconButton("mdi6.circle-outline", "Přidat kontrolu")
        self.addctrl_btn.clicked.connect(self.new_control_win.show)
        toolbar.addWidget(self.addctrl_btn)

        self.addstart_btn = QTAIconButton("mdi6.triangle-outline", "Přidat start")
        self.addstart_btn.clicked.connect(lambda: self.set_map_mode(MapWindowClickModes.ADD_START))
        toolbar.addWidget(self.addstart_btn)

        self.addfinish_btn = QTAIconButton("mdi6.circle-double", "Přidat cíl")
        self.addfinish_btn.clicked.connect(lambda: self.set_map_mode(MapWindowClickModes.ADD_FINISH))
        toolbar.addWidget(self.addfinish_btn)

        self.map_view = QQuickWidget()
        self.map_view.setResizeMode(QQuickWidget.ResizeMode.SizeRootObjectToView)
        maplayout.addWidget(self.map_view)

        self.map_handler = MapHandler(self)

        self.map_view.rootContext().setContextProperty("mapHandler", self.map_handler)
        self.qml_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "qml/Map.qml"))
        self.map_view.setSource(QUrl.fromLocalFile(self.qml_path))

        categories_lay = QVBoxLayout()
        layout.addLayout(categories_lay)

        catdetails_lay = QHBoxLayout()
        categories_lay.addLayout(catdetails_lay)
        catdetails_lay.addWidget(QLabel("Zvoleno:"))
        self.category_name_lbl = QLabel("")
        catdetails_lay.addWidget(self.category_name_lbl)
        catdetails_lay.addStretch()
        self.category_length_lbl = QLabel("")
        catdetails_lay.addWidget(self.category_length_lbl)

        self.categories_table = QTableWidget()
        self.categories_table.itemDoubleClicked.connect(self.table_dbl_click)
        categories_lay.addWidget(self.categories_table, stretch=4)

        categories_lay.addWidget(QLabel("Problémy:"))

        self.problems_list = QListWidget()
        categories_lay.addWidget(self.problems_list, stretch=2)

    def table_dbl_click(self, item: QTableWidgetItem):
        category_item = self.categories_table.item(item.row(), 0)
        if category_item:
            self.selected_category = category_item.text()
            self.change_category()

    def change_category(self):
        self.category_name_lbl.setText(self.selected_category)
        self.category_length_lbl.setText(routes.get_lenght_str(self.mw.db, self.selected_category))
        starts_finishes = api.get_starts_finishes(self.mw.db)
        if self.mw.map_win.selected_category and (
                not starts_finishes["categories"].get(self.mw.map_win.selected_category)) and len(
            starts_finishes["starts"]) and len(starts_finishes["finishes"]):
            starts_finishes["categories"][self.mw.map_win.selected_category] = {"start": 0, "finish": 0}
            api.set_basic_info(self.mw.db, {"map_starts_finishes": json.dumps(starts_finishes)})
        self.map_handler.update_map_items()
        self.update_categories()
        self.update_problems()

    def set_map_mode(self, map_mode: MapWindowClickModes):
        self.mode = map_mode

    def _show(self):
        self.update_categories()
        self.update_problems()
        self.change_category()
        self.map_handler.update_map_items(True)

    def update_categories(self):
        with Session(self.mw.db) as sess:
            categories = sess.scalars(Select(Category)).all()

            self.categories_table.clear()
            self.categories_table.setRowCount(len(categories))
            self.categories_table.setColumnCount(2)
            self.categories_table.setHorizontalHeaderLabels(["Kategorie", "Délka"])
            self.categories_table.verticalHeader().hide()
            self.categories_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
            self.categories_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.categories_table.setSelectionBehavior(QAbstractItemView.SelectRows)

            if categories and not self.selected_category:
                self.selected_category = categories[0].name

            for i, cat in enumerate(categories):
                self.categories_table.setItem(i, 0, QTableWidgetItem(cat.name))
                self.categories_table.setItem(i, 1, QTableWidgetItem(routes.get_lenght_str(self.mw.db, cat.name)))

    def update_problems(self):
        points = []

        starts_finishes = api.get_starts_finishes(self.mw.db)
        for i, start in enumerate(starts_finishes["starts"]):
            points.append((f"S{i + 1}", start["lat"], start["lon"], True))
        with Session(self.mw.db) as sess:
            conts = sess.scalars(Select(Control)).all()
            for cont in conts:
                if cont.lat and cont.lon:
                    points.append((cont.name, cont.lat, cont.lon, False))

        self.problems_list.clear()

        startdist = self.settings_win.start_edit.value()
        controldist = self.settings_win.control_edit.value()

        for point1, point2 in itertools.combinations(points, 2):
            if point1[3] and point2[3]: continue
            mindist = startdist if point1[3] or point2[3] else controldist
            dist = r_routes.point_dist(r_routes.Point(0, point1[1], point1[2]),
                                       r_routes.Point(1, point2[1], point2[2])) * 1000

            if dist < mindist:
                self.problems_list.addItem(QListWidgetItem(f"{point1[0]} -> {point2[0]}: {int(dist)} m < {mindist} m"))

    def open_map(self):
        dlg = QFileDialog(self, "Otevřít mapu")

        dlg.setFileMode(QFileDialog.FileMode.ExistingFile)
        dlg.setNameFilter("Rastrové mapy (*.png *.jpg *.tiff);;All files (*)")
        if dlg.exec():
            selected = dlg.selectedFiles()
            if not selected:
                return
            map_file = selected[0]

            srs, ok = QInputDialog.getText(
                self,
                "Vyberte SRS",
                "Zadejte kód souřadnicového systému:\n(Zrušte pro výchozí S-JTSK / Křovák / EPSG:5514)",
            )

            geo_mapper = GeoMapper(map_file, srs or "EPSG:5514")
            if root := self.map_view.rootObject():
                map_obj = root.findChild(QObject, "map")
                map_obj.addMap(json.dumps(geo_mapper.asdict()))
            self.map_handler.update_map_items()
