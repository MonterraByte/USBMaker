#   Copyright © 2017-2018 Joaquim Monteiro
#
#   This file is part of USBMaker.
#
#   USBMaker is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   USBMaker is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with USBMaker.  If not, see <https://www.gnu.org/licenses/>.

from PyQt5 import QtWidgets, QtGui
from about_ui import Ui_About
from license_ui import Ui_License


class About(QtWidgets.QWidget, Ui_About):
    def __init__(self):
        super(About, self).__init__()

        self.setupUi(self)

        self.license_window = License()

        if QtGui.QIcon.hasThemeIcon('usbmaker'):
            self.setWindowIcon(QtGui.QIcon.fromTheme('usbmaker'))
            self.license_window.setWindowIcon(QtGui.QIcon.fromTheme('usbmaker'))

        self.pushButton_close.clicked.connect(self.close)
        self.pushButton_about_qt.clicked.connect(QtWidgets.QApplication.aboutQt)
        self.pushButton_license.clicked.connect(self.license_window.show)


class License(QtWidgets.QDialog, Ui_License):
    def __init__(self):
        super(License, self).__init__()

        self.setupUi(self)

        self.pushButton_close.clicked.connect(self.close)
