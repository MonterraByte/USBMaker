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

        self.pushButton_close.clicked.connect(self.close)

        self.comboBox_partscheme.insertItem(0, 'MBR partition scheme for BIOS or UEFI')
        self.comboBox_partscheme.insertItem(1, 'MBR partition scheme for UEFI')
        self.comboBox_partscheme.insertItem(2, 'GPT partition scheme for UEFI')

        self.comboBox_filesystem.insertItem(0, 'FAT')
        self.comboBox_filesystem.insertItem(1, 'FAT32')
        self.comboBox_filesystem.insertItem(2, 'NTFS')
        self.comboBox_filesystem.insertItem(3, 'UDF')
        self.comboBox_filesystem.insertItem(4, 'exFAT')

        self.comboBox_checkbadblocks.insertItem(0, '1 Pass')
        self.comboBox_checkbadblocks.insertItem(1, '2 Passes')
        self.comboBox_checkbadblocks.insertItem(2, '3 Passes')
        self.comboBox_checkbadblocks.insertItem(3, '4 Passes')

        self.update_gui()
        self.comboBox_bootmethod.setCurrentIndex(0)

        self.comboBox_filesystem.currentIndexChanged.connect(self.update_gui)
        self.comboBox_partscheme.currentIndexChanged.connect(self.update_gui)

        for device in usb_info.get_id_list():
            self.comboBox_device.addItem('(' + str(round(usb_info.get_size(device)/1073741824, 1)) + 'GiB) ' + device)

    def update_gui(self):
        bootmethod_current_index = self.comboBox_bootmethod.currentIndex()
        self.comboBox_bootmethod.clear()
        self.comboBox_bootmethod.insertItem(0, 'ISO Image')
        self.comboBox_bootmethod.insertItem(1, 'DD Image')
        self.comboBox_bootmethod.insertItem(2, 'UEFI:NTFS')
        if self.comboBox_partscheme.currentText() == 'MBR partition scheme for BIOS or UEFI':
            self.comboBox_bootmethod.insertItem(3, 'FreeDOS')
            self.comboBox_bootmethod.insertItem(4, 'Syslinux 4.07')
            self.comboBox_bootmethod.insertItem(5, 'Syslinux 6.03')
            self.comboBox_bootmethod.insertItem(6, 'ReactOS')
            self.comboBox_bootmethod.insertItem(7, 'Grub 2.02 ~beta3')
            self.comboBox_bootmethod.insertItem(8, 'Grub4DOS 0.4.6a')
        self.comboBox_bootmethod.setCurrentIndex(0)
        if bootmethod_current_index <= self.comboBox_bootmethod.count():
            self.comboBox_bootmethod.setCurrentIndex(bootmethod_current_index)

        if self.comboBox_filesystem.currentText() == 'exFAT' or self.comboBox_filesystem.currentText() == 'UDF':
            self.checkBox_bootmethod.setCheckable(False)
            self.comboBox_bootmethod.clear()
        else:
            self.checkBox_bootmethod.setCheckable(True)


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()

window.show()
sys.exit(app.exec_())
