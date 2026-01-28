import random
from datetime import timedelta, datetime

from PySide6.QtCore import Qt, QPointF, QCoreApplication
from PySide6.QtGui import QBrush, QColor, QPen, QPainter, QFontMetrics
from PySide6.QtWidgets import (
    QWidget, QGraphicsRectItem, QGraphicsTextItem, QGraphicsScene, QGraphicsView, QVBoxLayout, QDoubleSpinBox, QLabel,
    QFormLayout, QPushButton, QGraphicsItem, QMessageBox,
)
from sqlalchemy import Select, Update
from sqlalchemy.orm import Session

import api
from models import Category, Runner

COLORS = [Qt.GlobalColor.red, Qt.GlobalColor.darkGreen, Qt.GlobalColor.darkBlue, Qt.GlobalColor.darkMagenta,
          Qt.GlobalColor.darkYellow, Qt.GlobalColor.darkCyan]

LINE_HEIGHT = 60
FIVE_MINUTES = 50
HEADER_HEIGHT = 20


class DrawClassDetailWindow(QWidget):
    def __init__(self, draw_class: DrawClass):
        super().__init__()

        self.draw_class = draw_class

        self.setWindowTitle(f"Detail kategorie {self.draw_class.text.toPlainText()}")

        lay = QFormLayout()
        self.setLayout(lay)

        lay.addWidget(QLabel(f"{self.draw_class.text.toPlainText()}"))

        self.interval_edit = QDoubleSpinBox()
        self.interval_edit.setSingleStep(0.5)

        lay.addRow("Interval (min):", self.interval_edit)

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.ok)
        lay.addWidget(ok_btn)

    def show(self):
        self.interval_edit.setValue(self.draw_class.interval)
        super().show()

    def ok(self):
        self.draw_class.interval = self.interval_edit.value()
        self.close()


class DrawClass(QGraphicsRectItem):
    def __init__(self, name, runners, scene: TimetableScene):
        super().__init__()

        self._runners = runners
        self.name = name
        self.sc = scene

        self.setBrush(QBrush(QColor(100, 150, 255, 200)))
        self.setPen(QPen(QColor('white'), 2))

        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)

        self.text = QGraphicsTextItem(name, self)
        self.text.setDefaultTextColor(QColor('white'))

        self.details_win = DrawClassDetailWindow(self)

        self.update_tooltip()

    def update_tooltip(self, newpos: QPointF = None):
        if newpos is not None:
            time = newpos.x() // (FIVE_MINUTES / 5)
        else:
            time = None
        date_tzero = datetime.fromisoformat(api.get_basic_info(self.sc.mw.db)["date_tzero"])
        starttime = date_tzero + timedelta(minutes=time or self.time)
        endtime = starttime + timedelta(minutes=self.runners * self.interval)

        self.setToolTip(
            f"{starttime.strftime("%H:%M:%S")} - {endtime.strftime("%H:%M:%S")}\nPočet závodníků: {self.runners}\nInterval: {self.interval} min")

    @property
    def time(self):
        return self.x() // (FIVE_MINUTES / 5)

    @time.setter
    def time(self, value: float):
        self.setX(value * (FIVE_MINUTES / 5))
        self.update_tooltip()

    @property
    def line(self):
        return self.y() // LINE_HEIGHT

    @line.setter
    def line(self, value: int):
        self.setY(value * LINE_HEIGHT)
        self.update_tooltip()

    @property
    def runners(self):
        return self._runners

    @runners.setter
    def runners(self, value: int):
        self._runners = value
        self.setRect(0, 0, value * self.interval * FIVE_MINUTES / 5, LINE_HEIGHT)
        self.update_tooltip()

    @property
    def interval(self):
        return self.rect().width() * 5 / (self.runners * FIVE_MINUTES)

    @interval.setter
    def interval(self, value: float):
        if self.y() != 0:
            self.setRect(0, 0, self.runners * value * (FIVE_MINUTES / 5), LINE_HEIGHT)
        self.update_tooltip()
        self.recolor()

    def recolor(self, pos=None):
        pos = pos or self.pos()
        if pos.y() == 0:
            self.setBrush(QBrush(QColor(100, 255, 150, 200)))
        elif self.interval != self.sc.baseint:
            self.setBrush(QBrush(QColor(255, 150, 100, 200)))
        else:
            self.setBrush(QBrush(QColor(100, 150, 255, 200)))

    def mouseDoubleClickEvent(self, event):
        self.details_win.show()
        super().mouseDoubleClickEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            new_pos = value
            new_pos.setX(
                max(0, round(new_pos.x() / (FIVE_MINUTES / (5 / self.sc.baseint))) * (
                        FIVE_MINUTES / (5 / self.sc.baseint))))
            new_pos.setY(max(0, round(new_pos.y() / LINE_HEIGHT) * LINE_HEIGHT))
            for cls in self.sc.classes:
                if cls is self or cls.y() != new_pos.y():
                    continue
                diff = new_pos.x() - cls.x()
                if 0 < diff < cls.rect().width():
                    new_pos.setX(cls.x() + cls.rect().width())
                elif diff <= 0 and -diff < self.rect().width():
                    new_pos.setX(cls.x() - self.rect().width())

            if new_pos.y() == 0:
                self.setRect(0, 0, FIVE_MINUTES, LINE_HEIGHT)
            elif self.y() == 0:
                self.setRect(0, 0, self.runners * self.sc.baseint * (FIVE_MINUTES / 5), LINE_HEIGHT)

            self.recolor(new_pos)

            self.update_tooltip()
            return new_pos
        return super().itemChange(change, value)


class TimetableScene(QGraphicsScene):
    def __init__(self, classes_num, baseint, mw):
        super().__init__()
        self.mw = mw
        self.classes = []
        self.baseint = baseint
        self.classes_num = classes_num + 1
        self.setSceneRect(0, -HEADER_HEIGHT, 8640 * FIVE_MINUTES, self.classes_num * LINE_HEIGHT + HEADER_HEIGHT)
        self.draw_grid()

    def draw_grid(self):
        all_minutes = 8640 * FIVE_MINUTES
        all_lines = self.classes_num * LINE_HEIGHT
        pen = QPen(QColor(230, 230, 230), 1)
        for i in range(0, all_lines + 1, LINE_HEIGHT):
            self.addLine(0, i, all_minutes, i, pen)

        for j in range(0, all_minutes + 1, FIVE_MINUTES):
            self.addLine(j, 0, j, all_lines, pen)

    def addClass(self, cls: DrawClass, i):
        self.addItem(cls)
        self.classes.append(cls)

        cls.itemChange(QGraphicsItem.GraphicsItemChange.ItemPositionChange, QPointF(0, 0))
        cls.setX(i * FIVE_MINUTES)

    def clear(self):
        super().clear()
        self.classes = []


class StartlistDrawWindow(QWidget):
    def __init__(self, mw):
        super().__init__()

        self.mw = mw

        lay = QVBoxLayout()
        self.setLayout(lay)

        self.setWindowTitle("Startovní listina - losování")

        lay.addWidget(QLabel("Základní interval (součet relací všech kontrol):"))

        self.base_interval_edit = QDoubleSpinBox()
        self.base_interval_edit.setSingleStep(0.5)
        self.base_interval_edit.setValue(5.0)
        self.base_interval_edit.editingFinished.connect(self.change_interval)
        lay.addWidget(self.base_interval_edit)

        draw_btn = QPushButton(QCoreApplication.translate("StartlistDrawWindow", "Losovat!"))
        draw_btn.clicked.connect(self._draw)
        lay.addWidget(draw_btn)

        self.view = TimetableView(self)
        lay.addWidget(self.view)

    def change_interval(self, *args):
        old_baseint = self.scene.baseint
        self.scene.baseint = self.base_interval_edit.value()
        for cls in self.scene.classes:
            if cls.interval == old_baseint:
                cls.interval = self.base_interval_edit.value()

    def show(self):
        super().showMaximized()
        with Session(self.mw.db) as sess:
            clss = sess.scalars(Select(Category).where(Category.runners.any())).all()
            try:
                self.date_tzero = datetime.fromisoformat(api.get_basic_info(self.mw.db)["date_tzero"])
            except Exception:
                self.date_tzero = datetime.now()

            self.scene = TimetableScene(len(clss), self.base_interval_edit.value(), self.mw)
            for i, cls in enumerate(clss):
                self.scene.addClass(DrawClass(cls.name, len(cls.runners), self.scene), i)

        self.view.setScene(self.scene)

        self.view.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.view.horizontalScrollBar().setValue(0)
        self.view.verticalScrollBar().setValue(0)

    def draw_category(self, cat_name, cat_zero, baseint_delta):
        last = cat_zero
        with Session(self.mw.db) as sess:
            cat = sess.scalars(
                Select(Category).where(Category.name == cat_name)
            ).first()
            runners = list(
                sess.scalars(Select(Runner).where(Runner.category == cat)).all()
            )

            clubs_dict = {}

            for runner in runners:
                if runner.club not in clubs_dict:
                    clubs_dict[runner.club] = [runner]
                else:
                    clubs_dict[runner.club].append(runner)

            clubs = list(clubs_dict.values())

            clubs.sort(key=len, reverse=True)

            i = 0
            while len(clubs) != 0:
                for club in clubs:
                    random.shuffle(club)
                    club[0].startlist_time = last
                    last = club[0].startlist_time + baseint_delta
                    club.pop(0)
                    i += 1
                while [] in clubs:
                    clubs.remove([])
            sess.commit()
        return last

    def _draw(self):
        zero = datetime.fromisoformat(api.get_basic_info(self.mw.db)["date_tzero"])
        with Session(self.mw.db) as sess:
            for cls in self.scene.classes:
                if cls.y() != 0:
                    self.draw_category(cls.name, zero + timedelta(minutes=cls.time), timedelta(minutes=cls.interval))
                else:
                    sess.execute(Update(Runner).where(Runner.category.has(name=cls.name)).values(
                        startlist_time=None))

            sess.commit()

        self.mw.startlist_win._update_startlist()

        QMessageBox.information(self, QCoreApplication.translate("StartlistDrawWindow", "Hotovo"),
                                QCoreApplication.translate("StartlistDrawWindow",
                                                           "Losování dokončeno, startovní časy byly přiřazeny"))

        self.close()


class TimetableView(QGraphicsView):
    def __init__(self, owner_window: StartlistDrawWindow):
        super().__init__()
        self.owner = owner_window

    def drawForeground(self, painter: QPainter, rect):
        super().drawForeground(painter, rect)
        if not hasattr(self.owner, 'scene') or self.owner.scene is None:
            return

        visible = self.mapToScene(self.viewport().rect()).boundingRect()
        left = max(0, int(visible.left()))
        right = max(0, int(visible.right()))

        start_j = (left // FIVE_MINUTES) * FIVE_MINUTES
        end_j = ((right // FIVE_MINUTES) + 1) * FIVE_MINUTES

        date_tzero = getattr(self.owner, 'date_tzero', None)
        if date_tzero is None:
            try:
                date_tzero = datetime.fromisoformat(api.get_basic_info(self.owner.mw.db)["date_tzero"])
            except Exception:
                date_tzero = datetime.now()

        painter.save()
        pen = QPen(QColor(120, 120, 120))
        painter.setPen(pen)
        font = painter.font()
        font.setPointSize(9)
        painter.setFont(font)
        fm = QFontMetrics(font)

        for j in range(start_j, end_j + 1, FIVE_MINUTES):
            minutes = (j // FIVE_MINUTES) * 5
            t = date_tzero + timedelta(minutes=minutes)
            label = t.strftime("%H:%M")

            pt = self.mapFromScene(QPointF(j, 0))
            x_view = pt.x()
            text_w = fm.horizontalAdvance(label)
            x_text = int(round(x_view - text_w / 2))
            painter.drawText(x_text, -4, label)

        painter.restore()
