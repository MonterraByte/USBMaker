#!/usr/bin/env python3
#   Copyright © 2017 Joaquim Monteiro
#
#   This file is part of USBMaker.
#
#   PyRufus is free software: you can redistribute it and/or modify
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

import sys
from PyQt5 import QtWidgets
from gui import Ui_MainWindow
import usb_info


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setupUi(self)

        self.comboBox_partscheme.insertItem(0, "MBR partition scheme for BIOS or UEFI")
        self.comboBox_partscheme.insertItem(1, "MBR partition scheme for UEFI")
        self.comboBox_partscheme.insertItem(2, "GPT partition scheme for UEFI")

        self.comboBox_filesystem.insertItem(0, "FAT")
        self.comboBox_filesystem.insertItem(1, "FAT32")
        self.comboBox_filesystem.insertItem(2, "NTFS")
        self.comboBox_filesystem.insertItem(3, "UDF")
        self.comboBox_filesystem.insertItem(4, "exFAT")

        self.comboBox_checkbadblocks.insertItem(0, "1 Pass")
        self.comboBox_checkbadblocks.insertItem(1, "2 Passes")
        self.comboBox_checkbadblocks.insertItem(2, "3 Passes")
        self.comboBox_checkbadblocks.insertItem(3, "4 Passes")

        for device in usb_info.get_id_list():
            self.comboBox_device.addItem('(' + str(round(usb_info.get_size(device)/1073741824, 1)) + 'GiB) ' + device)


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()

window.show()
sys.exit(app.exec_())