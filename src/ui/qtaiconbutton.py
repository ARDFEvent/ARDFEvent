import qtawesome as qta
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QPushButton, QHBoxLayout


class QTAIconButton(QPushButton):
    def __init__(self, icon, tooltip, icon_size=30, icon_margin=4, icon_optns=None, parent=None, extra_width=0,
                 color=None):
        super().__init__(parent)
        self._icon_size = int(icon_size)
        self._icon_margin = int(icon_margin)

        ico = None

        if type(icon) == str:
            if color:
                ico = qta.icon(icon, color=color)
            else:
                ico = qta.icon(icon)
        else:
            if icon_optns:
                ico = qta.icon(*icon, options=icon_optns)
            else:
                ico = qta.icon(*icon)

        self.setIcon(ico)

        self.setToolTip(tooltip)

        icon_qsize = QSize(self._icon_size, self._icon_size)
        self.setIconSize(icon_qsize)

        total = self._icon_size + 2 * self._icon_margin
        size = QSize(total + extra_width, total)
        self.setFixedSize(size)

    def sizeHint(self):
        total = self._icon_size + 2 * self._icon_margin
        return QSize(total, total)


class AlignedQTAIconButton(QTAIconButton):
    LEFT = 0
    CENTER = 1
    RIGHT = 2

    def __init__(self, icon, tooltip, align, icon_size=24, icon_margin=4, parent=None):
        super().__init__(icon, tooltip, icon_size, icon_margin, parent)

        self.lay = QHBoxLayout()

        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(0)

        if align == self.CENTER or align == self.RIGHT:
            self.lay.addStretch()

        self.lay.addWidget(self)

        if align == self.CENTER or align == self.LEFT:
            self.lay.addStretch()

    def btn_lay(self):
        return self.lay
