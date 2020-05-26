#!/usr/bin/env python3
#   Copyright © 2017-2020 Joaquim Monteiro
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

import sys
import os
import re
import subprocess
import shutil
from PyQt5 import QtWidgets, QtCore, QtGui
from gui import Ui_MainWindow
import about
import usb_info


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setupUi(self)

        if QtGui.QIcon.hasThemeIcon('usbmaker'):
            self.setWindowIcon(QtGui.QIcon.fromTheme('usbmaker'))

        self.about_window = about.About()

        # Here we set up the gui elements that aren't modified
        # elsewhere in the code.
        self.pushButton_close.clicked.connect(self.close)
        self.pushButton_about.clicked.connect(self.show_about_window)

        self.comboBox_partscheme.insertItem(0, 'MBR partition scheme for BIOS or UEFI')
        self.comboBox_partscheme.insertItem(1, 'MBR partition scheme for UEFI')
        self.comboBox_partscheme.insertItem(2, 'GPT partition scheme for BIOS or UEFI')
        self.comboBox_partscheme.insertItem(3, 'GPT partition scheme for UEFI')

        self.comboBox_filesystem.insertItem(0, 'Btrfs')
        self.comboBox_filesystem.insertItem(1, 'exFAT')
        self.comboBox_filesystem.insertItem(2, 'ext2')
        self.comboBox_filesystem.insertItem(3, 'ext3')
        self.comboBox_filesystem.insertItem(4, 'ext4')
        self.comboBox_filesystem.insertItem(5, 'F2FS')
        self.comboBox_filesystem.insertItem(6, 'FAT32')
        self.comboBox_filesystem.insertItem(7, 'NTFS')
        self.comboBox_filesystem.insertItem(8, 'UDF')
        self.comboBox_filesystem.insertItem(9, 'XFS')

        self.comboBox_bootmethod.insertItem(0, 'ISO Image')
        self.comboBox_bootmethod.insertItem(1, 'DD Image')

        self.homedir = os.path.expanduser('~')

        # self.device_id_list is initialized here.
        self.device_id_list = []

        # Here self.filename is initialized and the file dialog button
        # is set to activate the get_file_name function when clicked.
        self.filename = ''
        self.pushButton_filedialog.clicked.connect(self.get_file_name)

        # Changes to these parts of the gui trigger the update_gui function
        # to update the gui according to the selected options.
        self.comboBox_filesystem.currentIndexChanged.connect(self.update_gui)
        self.comboBox_partscheme.currentIndexChanged.connect(self.update_gui)
        self.comboBox_bootmethod.currentIndexChanged.connect(self.update_gui)
        self.checkBox_bootmethod.stateChanged.connect(self.update_gui)
        self.checkBox_checkbadblocks.stateChanged.connect(self.update_gui)

        # update_gui is called to finish the initialization of the gui.
        self.update_gui()

        # The available usb devices are detected here.
        self.refresh_device_list()
        # The refresh button is connected to the refresh_device_list function.
        self.pushButton_refresh.clicked.connect(self.refresh_device_list)

        # The start button is connected to the start function.
        #self.pushButton_start.clicked.connect(self.start)

    def update_gui(self):
        # This function is used to update/initialize the parts of the gui
        # that can be/are changed throughout the code.

        # Here the trigger for update_gui is disabled because otherwise
        # this function would trigger itself.
        self.comboBox_filesystem.currentIndexChanged.disconnect()
        self.comboBox_partscheme.currentIndexChanged.disconnect()
        self.comboBox_bootmethod.currentIndexChanged.disconnect()
        self.checkBox_bootmethod.stateChanged.disconnect()
        self.checkBox_checkbadblocks.stateChanged.disconnect()

        if self.comboBox_filesystem.currentText() == 'ext2' \
        or self.comboBox_filesystem.currentText() == 'ext3' \
        or self.comboBox_filesystem.currentText() == 'ext4' \
        or self.comboBox_filesystem.currentText() == 'FAT32' \
        or self.comboBox_filesystem.currentText() == 'NTFS':
            self.checkBox_checkbadblocks.setEnabled(True)
        else:
            self.checkBox_checkbadblocks.setEnabled(False)

        if self.comboBox_bootmethod.currentText() == "DD Image" and self.checkBox_bootmethod.isChecked():
            # Most of the gui is disabled if "DD Image" is selected.
            self.comboBox_partscheme.setEnabled(False)
            self.comboBox_filesystem.setEnabled(False)
            self.checkBox_checkbadblocks.setEnabled(False)
            self.lineEdit_label.setEnabled(False)
        else:
            self.comboBox_partscheme.setEnabled(True)
            self.comboBox_filesystem.setEnabled(True)
            self.lineEdit_label.setEnabled(True)

            if self.comboBox_filesystem.currentText() == 'exFAT' or self.comboBox_filesystem.currentText() == 'UDF':
                # exFAT or UDF aren't bootable, so comboBox_bootmethod
                # checkBox_bootmethod are disabled.
                self.checkBox_bootmethod.setEnabled(False)
                self.comboBox_bootmethod.setEnabled(False)
            else:
                self.checkBox_bootmethod.setEnabled(True)
                self.comboBox_bootmethod.setEnabled(True)

        if not self.checkBox_bootmethod.isEnabled() or not self.checkBox_bootmethod.isChecked():
            self.comboBox_bootmethod.setEnabled(False)
            self.pushButton_filedialog.setEnabled(False)
        else:
            self.comboBox_bootmethod.setEnabled(True)
            self.pushButton_filedialog.setEnabled(True)

        # Here the trigger for update_ui is re-enabled.
        self.comboBox_filesystem.currentIndexChanged.connect(self.update_gui)
        self.comboBox_partscheme.currentIndexChanged.connect(self.update_gui)
        self.comboBox_bootmethod.currentIndexChanged.connect(self.update_gui)
        self.checkBox_bootmethod.stateChanged.connect(self.update_gui)
        self.checkBox_checkbadblocks.stateChanged.connect(self.update_gui)

    def disable_gui(self):
        self.pushButton_start.setEnabled(False)
        self.pushButton_refresh.setEnabled(False)
        self.pushButton_filedialog.setEnabled(False)
        self.pushButton_close.setEnabled(False)
        self.comboBox_device.setEnabled(False)
        self.comboBox_partscheme.setEnabled(False)
        self.comboBox_filesystem.setEnabled(False)
        self.comboBox_bootmethod.setEnabled(False)
        self.lineEdit_label.setEnabled(False)
        self.checkBox_checkbadblocks.setEnabled(False)
        self.checkBox_bootmethod.setEnabled(False)

    def enable_gui(self):
        self.pushButton_start.setEnabled(True)
        self.pushButton_refresh.setEnabled(True)
        self.pushButton_filedialog.setEnabled(True)
        self.pushButton_close.setEnabled(True)
        self.comboBox_device.setEnabled(True)
        self.comboBox_partscheme.setEnabled(True)
        self.comboBox_filesystem.setEnabled(True)
        self.comboBox_bootmethod.setEnabled(True)
        self.lineEdit_label.setEnabled(True)
        self.checkBox_checkbadblocks.setEnabled(True)
        self.checkBox_bootmethod.setEnabled(True)

        self.update_gui()

    @QtCore.pyqtSlot(bool)
    def set_enabled(self, enable):
        if enable:
            self.enable_gui()
        else:
            self.disable_gui()

    @QtCore.pyqtSlot(int)
    def set_progress(self, value):
        self.progressBar.setValue(value)

    @QtCore.pyqtSlot(str)
    def set_status(self, text):
        self.label_status.setText(text)

    def show_about_window(self):
        center_point_x = int(self.x() + self.width() / 2)
        center_point_y = int(self.y() + self.height() / 2)
        x = int(center_point_x - self.about_window.width() / 2)
        y = int(center_point_y - self.about_window.height() / 2)
        self.about_window.move(x, y)
        self.about_window.show()

    def show_messagebox(self, messagebox):
        center_point_x = int(self.x() + self.width() / 2)
        center_point_y = int(self.y() + self.height() / 2)
        # The message box needs to be shown in order for width() and height()
        # to return the correct values.
        messagebox.show()
        x = int(center_point_x - messagebox.width() / 2)
        y = int(center_point_y - messagebox.height() / 2)
        messagebox.move(x, y)

    def refresh_device_list(self):
        self.device_id_list = usb_info.get_id_list()
        self.comboBox_device.clear()
        for device in self.device_id_list:
            self.comboBox_device.addItem('(' + str(round(usb_info.get_size(
                usb_info.get_block_device_name(device))/1073741824, 1)) + 'GiB) ' + device)

    def get_file_name(self):
        # getOpenFileName returns a tuple with the file path and the filter,
        # so to get only the file path we use [0].
        # If the user selects the cancel button, self.filename remains unchanged
        filename = QtWidgets.QFileDialog.getOpenFileName(directory=self.homedir,
                                                         filter='ISO Files (*.iso);;All Files (*)',
                                                         initialFilter='ISO Files (*.iso)')[0]
        if filename != '':
            # Only change self.filename if a file is actually selected.
            self.filename = filename

            if shutil.which('isoinfo') is not None:
                default_label = ''

                try:
                    isoinfo_output = subprocess.check_output(['isoinfo', '-d', '-i', self.filename]).decode()
                except subprocess.CalledProcessError:
                    # If the selected file is not an iso file, isoinfo will
                    # return a non-zero return code. If this exception isn't
                    # caught, the whole program will be terminated.
                    isoinfo_output = ''

                isoinfo_list = isoinfo_output.splitlines()
                for line in isoinfo_list:
                    if re.search('Volume id:', line):
                        default_label = line[11:]

                self.lineEdit_label.setText(default_label)


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()

window.show()
sys.exit(app.exec_())
