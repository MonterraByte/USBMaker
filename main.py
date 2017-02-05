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

        # Here we set up the gui elements that aren't modified
        # elsewhere in the code.
        self.pushButton_close.clicked.connect(self.close)

        self.comboBox_checkbadblocks.insertItem(0, '1 Pass')
        self.comboBox_checkbadblocks.insertItem(1, '2 Passes')
        self.comboBox_checkbadblocks.insertItem(2, '3 Passes')
        self.comboBox_checkbadblocks.insertItem(3, '4 Passes')

        # Changes to these parts of the gui trigger the update_gui function
        # to update the gui according to the selected options.
        self.comboBox_filesystem.currentIndexChanged.connect(self.update_gui)
        self.comboBox_partscheme.currentIndexChanged.connect(self.update_gui)
        self.comboBox_bootmethod.currentIndexChanged.connect(self.update_gui)

        # update_gui is called to finish the initialization of the gui.
        self.update_gui()

        # The available usb devices are detected here.
        for device in usb_info.get_id_list():
            self.comboBox_device.addItem('(' + str(round(usb_info.get_size(device)/1073741824, 1)) + 'GiB) ' + device)

    def update_gui(self):
        # This function is used to update/initialize the parts of the gui
        # that can be/are changed throughout the code.

        # Here the trigger for update_gui is disabled because otherwise
        # this function would trigger itself.
        self.comboBox_filesystem.currentIndexChanged.disconnect()
        self.comboBox_partscheme.currentIndexChanged.disconnect()
        self.comboBox_bootmethod.currentIndexChanged.disconnect()

        if self.comboBox_bootmethod.currentText() == "DD Image":
            # Most of the gui is disabled if "DD Image" is selected.
            self.comboBox_partscheme.clear()
            self.comboBox_filesystem.clear()
            self.comboBox_clustersize.clear()
            self.lineEdit_label.setReadOnly(True)
            self.lineEdit_label.clear()
            self.checkBox_quickformat.setCheckable(False)
            self.checkBox_quickformat.setChecked(False)
            self.checkBox_extlabel.setCheckable(False)
            self.checkBox_extlabel.setChecked(False)
        else:
            # The current index for each comboBox is stored before
            # its update and restored afterwards.
            partscheme_current_index = self.comboBox_partscheme.currentIndex()
            if partscheme_current_index == -1:
                # When update_ui is first executed (when the program is launched),
                # all indexes are set to -1, so we need to manually set them to 0.
                partscheme_current_index = 0
            self.comboBox_partscheme.clear()
            self.comboBox_partscheme.insertItem(0, 'MBR partition scheme for BIOS or UEFI')
            self.comboBox_partscheme.insertItem(1, 'MBR partition scheme for UEFI')
            self.comboBox_partscheme.insertItem(2, 'GPT partition scheme for UEFI')
            self.comboBox_partscheme.setCurrentIndex(partscheme_current_index)

            filesystem_current_index = self.comboBox_filesystem.currentIndex()
            if filesystem_current_index == -1:
                filesystem_current_index = 0
            self.comboBox_filesystem.clear()
            self.comboBox_filesystem.insertItem(0, 'FAT')
            self.comboBox_filesystem.insertItem(1, 'FAT32')
            self.comboBox_filesystem.insertItem(2, 'NTFS')
            self.comboBox_filesystem.insertItem(3, 'UDF')
            self.comboBox_filesystem.insertItem(4, 'exFAT')
            self.comboBox_filesystem.setCurrentIndex(filesystem_current_index)

            bootmethod_current_index = self.comboBox_bootmethod.currentIndex()
            if bootmethod_current_index == -1:
                bootmethod_current_index = 0
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
                # As the number of valid indexes may vary, the stored index is
                # only restored if it is valid. Otherwise it is set to 0.
                self.comboBox_bootmethod.setCurrentIndex(bootmethod_current_index)

            if self.comboBox_filesystem.currentText() == 'exFAT' or self.comboBox_filesystem.currentText() == 'UDF':
                # exFAT or UDF aren't bootable, so comboBox_bootmethod
                # checkBox_bootmethod are cleared.
                self.checkBox_bootmethod.setCheckable(False)
                self.checkBox_bootmethod.setChecked(False)
                self.comboBox_bootmethod.clear()
            else:
                # comboBox_bootmethod should be restored at this point,
                # so it's only necessary to restore checkBox_bootmethod.
                self.checkBox_bootmethod.setCheckable(True)

        # Here the trigger for update_ui is re-enabled.
        self.comboBox_filesystem.currentIndexChanged.connect(self.update_gui)
        self.comboBox_partscheme.currentIndexChanged.connect(self.update_gui)
        self.comboBox_bootmethod.currentIndexChanged.connect(self.update_gui)


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()

window.show()
sys.exit(app.exec_())
