import random
import string
import unittest
from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from dateutil.parser import parser

import api
# noinspection PyUnresolvedReferences
from ui import resources, resources_init
from ui.mainwin import MainWindow


class TestUI(unittest.TestCase):
    def setUp(self):
        app = QApplication()
        self.mainwin = MainWindow()
        self.mainwin.show("sqlite:///")

    def test_info_setting(self):
        race_name = ''.join(random.choices(string.printable, k=30))
        org_name = ''.join(random.choices(string.printable, k=30))
        self.mainwin.basicinfo_win.name_edit.setText(race_name)
        self.mainwin.basicinfo_win.date_edit.setDateTime(datetime(2025, 3, 10, 12))
        self.mainwin.basicinfo_win.org_edit.setText(org_name)
        QTest.mouseClick(self.mainwin.basicinfo_win.ok_btn, Qt.LeftButton)

        bi = api.get_basic_info(self.mainwin.db)

        self.assertEqual(bi["name"], race_name)
        self.assertEqual(parser().parse(bi["date_tzero"]).timestamp(), datetime(2025, 3, 10, 12).timestamp())


if __name__ == '__main__':
    unittest.main()
