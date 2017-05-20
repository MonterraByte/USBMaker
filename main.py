#!/usr/bin/env python3
#   Copyright © 2017 Joaquim Monteiro
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
from PyQt5 import QtWidgets, QtCore
from gui import Ui_MainWindow
import about
import usb_info
import partitioning
import formatting
import dd
import mount
import iso


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    # Signals have to be declared here.
    signal_format = QtCore.pyqtSignal(str, str, str, str, int, int, str)
    signal_dd = QtCore.pyqtSignal(str, str, int, str)
    signal_iso = QtCore.pyqtSignal(str, str, str, str, str, str, int, int, str, list, list, str)

    def __init__(self):
        super(MainWindow, self).__init__()

        self.setupUi(self)
        desktop_center = QtWidgets.QDesktopWidget().availableGeometry().center()
        self.move(int(desktop_center.x() - self.width() / 2), int(desktop_center.y() - self.height() / 2))

        self.about_window = about.About()

        # Here we set up the gui elements that aren't modified
        # elsewhere in the code.
        self.pushButton_close.clicked.connect(self.close)
        self.pushButton_about.clicked.connect(self.show_about_window)

        self.comboBox_partscheme.insertItem(0, 'MBR partition scheme for BIOS or UEFI')
        self.comboBox_partscheme.insertItem(1, 'MBR partition scheme for UEFI')
        self.comboBox_partscheme.insertItem(2, 'GPT partition scheme for BIOS or UEFI')
        self.comboBox_partscheme.insertItem(3, 'GPT partition scheme for UEFI')

        self.comboBox_filesystem.insertItem(0, 'FAT32')
        self.comboBox_filesystem.insertItem(1, 'FAT16')
        self.comboBox_filesystem.insertItem(2, 'NTFS')
        self.comboBox_filesystem.insertItem(3, 'UDF')
        self.comboBox_filesystem.insertItem(4, 'exFAT')
        self.comboBox_filesystem.insertItem(5, 'ext4')
        self.comboBox_filesystem.insertItem(6, 'Btrfs')

        self.comboBox_bootmethod.insertItem(0, 'ISO Image')
        self.comboBox_bootmethod.insertItem(1, 'DD Image')

        self.comboBox_checkbadblocks.insertItem(0, '1 Pass')
        self.comboBox_checkbadblocks.insertItem(1, '2 Passes')
        self.comboBox_checkbadblocks.insertItem(2, '3 Passes')
        self.comboBox_checkbadblocks.insertItem(3, '4 Passes')

        # Check for dependencies and their locations
        self.syslinux = ['', '', '']
        self.syslinux_modules = ['', '', '']
        self.grldr = ''
        self.get_dependencies()

        # The badblocks message box is initialized here.
        self.messageBox_badblocks = QtWidgets.QMessageBox()
        self.messageBox_badblocks.setStandardButtons(QtWidgets.QMessageBox.Close)

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
        self.comboBox_clustersize.currentIndexChanged.connect(self.update_gui)
        self.checkBox_bootmethod.stateChanged.connect(self.update_gui)
        self.checkBox_checkbadblocks.stateChanged.connect(self.update_gui)

        # update_gui is called to finish the initialization of the gui.
        self.update_gui()

        # The available usb devices are detected here.
        self.refresh_device_list()
        # The refresh button is connected to the refresh_device_list function.
        self.pushButton_refresh.clicked.connect(self.refresh_device_list)

        # The worker object is moved to a separate thread.
        self.worker = WorkerObject(self)
        self.thread = QtCore.QThread()
        self.worker.moveToThread(self.thread)

        # The signals emitted in the start_* functions are connected to the
        # corresponding functions from the worker object.
        self.signal_format.connect(self.worker.format)
        self.signal_dd.connect(self.worker.make_bootable_dd)
        self.signal_iso.connect(self.worker.make_bootable_iso)

        # The start button is connected to the start function.
        self.pushButton_start.clicked.connect(self.start)

    def get_dependencies(self):
        # Find syslinux
        messagebox_missingsyslinux = QtWidgets.QMessageBox(self)
        messagebox_missingsyslinux.setStandardButtons(QtWidgets.QMessageBox.Ok)

        messagebox_missingsyslinux.setWindowTitle('Syslinux is missing - USBMaker')
        messagebox_missingsyslinux\
            .setText('Syslinux was not found.\nThe creation of bootable drives with an ISO image may not work.')
        messagebox_missingsyslinux.setIcon(QtWidgets.QMessageBox.Warning)

        syslinux_not_found = False

        # self.syslinux contains the path to the directory containing the
        # syslinux mbr and the efi executables, in this format: [bios, efi64, efi32]
        # self.syslinux_modules contains the path to the module directory
        # in the format: [bios, efi64, efi32]
        self.syslinux = ['', '', '']
        self.syslinux_modules = ['', '', '']

        # MBR and EFI executables

        if os.path.exists('/usr/lib/syslinux/bios/mbr.bin'):
            self.syslinux[0] = '/usr/lib/syslinux/bios'
        elif os.path.exists('/usr/lib/syslinux/mbr/mbr.bin'):
            self.syslinux[0] = '/usr/lib/syslinux/mbr'
        elif os.path.exists('/usr/share/syslinux/mbr.bin'):
            self.syslinux[0] = '/usr/share/syslinux'
        else:
            self.syslinux[0] = ''
            syslinux_not_found = True

        if os.path.exists('/usr/lib/syslinux/efi64/syslinux.efi'):
            self.syslinux[1] = '/usr/lib/syslinux/efi64'
        elif os.path.exists('/usr/lib/SYSLINUX.EFI/efi64/syslinux.efi'):
            self.syslinux[1] = '/usr/lib/SYSLINUX.EFI/efi64'
        else:
            self.syslinux_[1] = ''
            syslinux_not_found = True

        if os.path.exists('/usr/lib/syslinux/efi32/syslinux.efi'):
            self.syslinux[2] = '/usr/lib/syslinux/efi32'
        elif os.path.exists('/usr/lib/SYSLINUX.EFI/efi32/syslinux.efi'):
            self.syslinux[2] = '/usr/lib/SYSLINUX.EFI/efi32'
        else:
            self.syslinux[2] = ''
            syslinux_not_found = True

        # Modules

        if os.path.isdir('/usr/lib/syslinux/bios'):
            for file in os.listdir('/usr/lib/syslinux/bios'):
                if re.search('c32', file):
                    self.syslinux_modules[0] = '/usr/lib/syslinux/bios'
                    break
        elif os.path.isdir('/usr/lib/syslinux/modules/bios'):
            for file in os.listdir('/usr/lib/syslinux/modules/bios'):
                if re.search('c32', file):
                    self.syslinux_modules[0] = '/usr/lib/syslinux/modules/bios'
                    break
        elif os.path.isdir('/usr/share/syslinux'):
            for file in os.listdir('/usr/share/syslinux'):
                if re.search('c32', file):
                    self.syslinux_modules[0] = '/usr/share/syslinux'
                    break
        else:
            self.syslinux_modules[0] = ''
            syslinux_not_found = True

        if os.path.isdir('/usr/lib/syslinux/efi64'):
            for file in os.listdir('/usr/lib/syslinux/efi64'):
                if re.search('c32', file):
                    self.syslinux_modules[1] = '/usr/lib/syslinux/efi64'
                    break
        elif os.path.isdir('/usr/lib/syslinux/modules/efi64'):
            for file in os.listdir('/usr/lib/syslinux/modules/efi64'):
                if re.search('c32', file):
                    self.syslinux_modules[1] = '/usr/lib/syslinux/modules/efi64'
                    break
        elif os.path.isdir('/usr/share/syslinux/efi64'):
            for file in os.listdir('/usr/share/syslinux/efi64'):
                if re.search('c32', file):
                    self.syslinux_modules[1] = '/usr/share/syslinux/efi64'
                    break
        else:
            self.syslinux_modules[1] = ''
            syslinux_not_found = True

        if os.path.isdir('/usr/lib/syslinux/efi32'):
            for file in os.listdir('/usr/lib/syslinux/efi32'):
                if re.search('c32', file):
                    self.syslinux_modules[2] = '/usr/lib/syslinux/efi32'
                    break
        elif os.path.isdir('/usr/lib/syslinux/modules/efi32'):
            for file in os.listdir('/usr/lib/syslinux/modules/efi32'):
                if re.search('c32', file):
                    self.syslinux_modules[2] = '/usr/lib/syslinux/modules/efi32'
                    break
        elif os.path.isdir('/usr/share/syslinux/efi32'):
            for file in os.listdir('/usr/share/syslinux/efi32'):
                if re.search('c32', file):
                    self.syslinux_modules[1] = '/usr/share/syslinux/efi32'
                    break
        else:
            self.syslinux_modules[2] = ''
            syslinux_not_found = True

        if syslinux_not_found:
            self.show_messagebox(messagebox_missingsyslinux)

        # Find grub4dos
        messagebox_missinggrub4dos = QtWidgets.QMessageBox(self)
        messagebox_missinggrub4dos.setStandardButtons(QtWidgets.QMessageBox.Ok)

        messagebox_missinggrub4dos.setWindowTitle('grub4dos is missing - USBMaker')
        messagebox_missinggrub4dos\
            .setText('grub4dos was not found.\nThe creation of bootable drives with an ISO image may not work.')
        messagebox_missinggrub4dos.setIcon(QtWidgets.QMessageBox.Warning)

        grub4dos_not_found = False

        # Check if either bootlace.com or bootlace64.com are on PATH.
        if shutil.which('bootlace64.com') is None or shutil.which('bootlace.com') is None:
            grub4dos_not_found = True

        # grldr
        if os.path.exists('/grub/grldr'):
            self.grldr = '/grub/grldr'
        else:
            self.grldr = ''
            grub4dos_not_found = True

        if grub4dos_not_found:
            self.show_messagebox(messagebox_missinggrub4dos)

        # Find grub2
        messagebox_missinggrub2 = QtWidgets.QMessageBox(self)
        messagebox_missinggrub2.setStandardButtons(QtWidgets.QMessageBox.Ok)

        messagebox_missinggrub2.setWindowTitle('GRUB2 is missing - USBMaker')
        messagebox_missinggrub2 \
            .setText('GRUB2 was not found.\nThe creation of bootable drives with an ISO image may not work.')
        messagebox_missinggrub2.setIcon(QtWidgets.QMessageBox.Warning)

        # Look for grub-install.
        if shutil.which('grub-install') is None:
            self.show_messagebox(messagebox_missinggrub2)

    def update_gui(self):
        # This function is used to update/initialize the parts of the gui
        # that can be/are changed throughout the code.

        # Here the trigger for update_gui is disabled because otherwise
        # this function would trigger itself.
        self.comboBox_filesystem.currentIndexChanged.disconnect()
        self.comboBox_partscheme.currentIndexChanged.disconnect()
        self.comboBox_bootmethod.currentIndexChanged.disconnect()
        self.comboBox_clustersize.currentIndexChanged.disconnect()
        self.checkBox_bootmethod.stateChanged.disconnect()
        self.checkBox_checkbadblocks.stateChanged.disconnect()

        if self.comboBox_bootmethod.currentText() == "DD Image" and self.checkBox_bootmethod.isChecked():
            # Most of the gui is disabled if "DD Image" is selected.
            self.comboBox_partscheme.setEnabled(False)
            self.comboBox_filesystem.setEnabled(False)
            self.comboBox_clustersize.setEnabled(False)
            self.lineEdit_label.setEnabled(False)
        else:
            self.comboBox_partscheme.setEnabled(True)
            self.comboBox_filesystem.setEnabled(True)
            self.comboBox_clustersize.setEnabled(True)
            self.lineEdit_label.setEnabled(True)

            # The current index for the cluster size comboBox is stored before
            # its update and restored afterwards.

            clustersize_current_index = self.comboBox_clustersize.currentIndex()
            if clustersize_current_index == -1:
                clustersize_current_index = 0
            self.comboBox_clustersize.clear()
            self.comboBox_clustersize.insertItem(0, 'Default')
            if self.comboBox_filesystem.currentText().lower() != 'exfat':
                if self.comboBox_filesystem.currentText().lower() != 'ext4':
                    self.comboBox_clustersize.insertItem(1, '512')
                self.comboBox_clustersize.insertItem(2, '1024')
                self.comboBox_clustersize.insertItem(3, '2048')
                self.comboBox_clustersize.insertItem(4, '4096')
                if self.comboBox_filesystem.currentText().lower() == 'ntfs' or \
                   self.comboBox_filesystem.currentText().lower() == 'fat32' or \
                   self.comboBox_filesystem.currentText().lower() == 'fat16' or \
                   self.comboBox_filesystem.currentText().lower() == 'btrfs':
                    self.comboBox_clustersize.insertItem(5, '8192')
                    self.comboBox_clustersize.insertItem(6, '16384')
                    self.comboBox_clustersize.insertItem(7, '32768')
                    self.comboBox_clustersize.insertItem(8, '65536')

            self.comboBox_clustersize.setCurrentIndex(0)
            if clustersize_current_index <= self.comboBox_clustersize.count():
                # As the number of valid indexes may vary, the stored index is
                # only restored if it is valid. Otherwise it is set to 0.
                self.comboBox_clustersize.setCurrentIndex(clustersize_current_index)

            if self.comboBox_filesystem.currentText() == 'exFAT' or self.comboBox_filesystem.currentText() == 'UDF':
                # exFAT or UDF aren't bootable, so comboBox_bootmethod
                # checkBox_bootmethod are disabled.
                self.checkBox_bootmethod.setEnabled(False)
                self.checkBox_bootmethod.setChecked(False)
                self.comboBox_bootmethod.setEnabled(False)
            else:
                self.checkBox_bootmethod.setEnabled(True)
                self.comboBox_bootmethod.setEnabled(True)

        if self.comboBox_clustersize.currentIndex() == 0:
            self.checkBox_checkbadblocks.setEnabled(False)
            self.checkBox_checkbadblocks.setChecked(False)
            self.comboBox_checkbadblocks.setEnabled(False)
        else:
            self.checkBox_checkbadblocks.setEnabled(True)
            self.comboBox_checkbadblocks.setEnabled(True)

        if not self.checkBox_bootmethod.isChecked():
            self.comboBox_bootmethod.setEnabled(False)
            self.pushButton_filedialog.setEnabled(False)
        else:
            self.comboBox_bootmethod.setEnabled(True)
            self.pushButton_filedialog.setEnabled(True)

        if not self.checkBox_checkbadblocks.isChecked():
            self.comboBox_checkbadblocks.setEnabled(False)
        else:
            self.comboBox_checkbadblocks.setEnabled(True)

        # Here the trigger for update_ui is re-enabled.
        self.comboBox_filesystem.currentIndexChanged.connect(self.update_gui)
        self.comboBox_partscheme.currentIndexChanged.connect(self.update_gui)
        self.comboBox_bootmethod.currentIndexChanged.connect(self.update_gui)
        self.comboBox_clustersize.currentIndexChanged.connect(self.update_gui)
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
        self.comboBox_clustersize.setEnabled(False)
        self.comboBox_checkbadblocks.setEnabled(False)
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
        self.comboBox_clustersize.setEnabled(True)
        self.comboBox_checkbadblocks.setEnabled(True)
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

    @QtCore.pyqtSlot(str)
    def show_badblocks_messagebox(self, badblocks_file):
        if os.path.getsize(badblocks_file) > 0:
            # There are bad blocks in the drive.
            self.messageBox_badblocks.setText('Bad blocks were found on the drive.')
            self.messageBox_badblocks.setIcon(QtWidgets.QMessageBox.Warning)
        else:
            # There aren't any bad blocks in the drive.
            self.messageBox_badblocks.setText('No bad blocks were found on the drive.')
            self.messageBox_badblocks.setIcon(QtWidgets.QMessageBox.Information)

        center_point_x = int(self.x() + self.width() / 2)
        center_point_y = int(self.y() + self.height() / 2)
        # The message box needs to be shown in order for width() and height()
        # to return the correct values.
        self.messageBox_badblocks.show()
        x = int(center_point_x - self.messageBox_badblocks.width() / 2)
        y = int(center_point_y - self.messageBox_badblocks.height() / 2)
        self.messageBox_badblocks.move(x, y)

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
        filename = QtWidgets.QFileDialog.getOpenFileName(directory=os.path.expanduser('~'),
                                                         filter='ISO Files (*.iso);;All Files (*)',
                                                         initialFilter='ISO Files (*.iso)')[0]
        if filename != '':
            # Only change self.filename if a file is actually selected.
            self.filename = filename

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

    def get_table(self):
        if self.comboBox_partscheme.currentIndex() == 0 or self.comboBox_partscheme.currentIndex() == 1:
            return 'msdos'
        else:
            return 'gpt'

    def get_badblocks_passes(self):
        if not self.checkBox_checkbadblocks.isChecked():
            return 0
        elif self.comboBox_checkbadblocks.currentIndex() == 1:
            return 2
        elif self.comboBox_checkbadblocks.currentIndex() == 2:
            return 3
        elif self.comboBox_checkbadblocks.currentIndex() == 3:
            return 4
        else:
            return 1

    def get_cluster_size(self):
        if self.comboBox_clustersize.currentText() == '512':
            return 512
        elif self.comboBox_clustersize.currentText() == '1024':
            return 1024
        elif self.comboBox_clustersize.currentText() == '2048':
            return 2048
        elif self.comboBox_clustersize.currentText() == '4096':
            return 4096
        elif self.comboBox_clustersize.currentText() == '8192':
            return 8192
        elif self.comboBox_clustersize.currentText() == '16384':
            return 16384
        elif self.comboBox_clustersize.currentText() == '32768':
            return 32768
        elif self.comboBox_clustersize.currentText() == '65536':
            return 65536
        else:
            return -1

    def get_label(self):
        return self.lineEdit_label.text()

    def get_device_id(self):
        return self.device_id_list[self.comboBox_device.currentIndex()]

    def get_filesystem(self):
        return self.comboBox_filesystem.currentText().lower()

    def get_target(self):
        if self.comboBox_partscheme.currentIndex() == 0 or self.comboBox_partscheme.currentIndex() == 2:
            return 'both'
        else:
            return 'uefi'

    def start_format(self):
        # Collect information.
        label = self.get_label()
        device_id = self.get_device_id()
        partition_table = self.get_table()
        filesystem = self.get_filesystem()
        device = usb_info.get_block_device_name(device_id)
        badblocks_passes = self.get_badblocks_passes()
        badblocks_file = '/tmp/usbmaker' + str(os.getpid()) + '-badblocks.txt'
        clustersize = self.get_cluster_size()

        # Send a signal to the worker object to start the format() function.
        self.signal_format.emit(device, filesystem, partition_table, label, clustersize, badblocks_passes,
                                badblocks_file)

    def start_dd(self):
        # Collect information.
        device_id = self.get_device_id()
        device = usb_info.get_block_device_name(device_id)
        badblocks_passes = self.get_badblocks_passes()
        badblocks_file = '/tmp/usbmaker' + str(os.getpid()) + '-badblocks.txt'

        # Send a signal to the worker object to start the make_bootable_dd() function.
        self.signal_dd.emit(device, self.filename, badblocks_passes, badblocks_file)

    def start_iso(self):
        # Collect information.
        label = self.get_label()
        device_id = self.get_device_id()
        partition_table = self.get_table()
        filesystem = self.get_filesystem()
        device = usb_info.get_block_device_name(device_id)
        badblocks_passes = self.get_badblocks_passes()
        badblocks_file = '/tmp/usbmaker' + str(os.getpid()) + '-badblocks.txt'
        clustersize = self.get_cluster_size()
        target = self.get_target()

        # Send a signal to the worker object to start the make_bootable_iso() function.
        self.signal_iso.emit(device, self.filename, filesystem, partition_table, target, label, clustersize,
                             badblocks_passes, badblocks_file, self.syslinux, self.syslinux_modules, self.grldr)

    def start(self):
        # Check if there's a device selected.
        if self.comboBox_device.currentText() != '':
            if self.checkBox_bootmethod.isChecked():
                # Check if there's a file selected.
                if self.filename != '':
                    if self.comboBox_bootmethod.currentText() == 'DD Image':
                        # Calling QThread.start() after the QThread is already started does nothing.
                        self.thread.start()
                        self.start_dd()
                    elif self.comboBox_bootmethod.currentText() == 'ISO Image':
                        # Calling QThread.start() after the QThread is already started does nothing.
                        self.thread.start()
                        self.start_iso()
                else:
                    # No file selected.
                    self.label_status.setText('Error: No file selected.')
            else:
                # Calling QThread.start() after the QThread is already started does nothing.
                self.thread.start()
                self.start_format()
        else:
            # No device selected.
            self.label_status.setText('Error: no device selected.')


class WorkerObject(QtCore.QObject):
    signal_set_enabled = QtCore.pyqtSignal(bool)
    signal_set_progress = QtCore.pyqtSignal(int)
    signal_set_status = QtCore.pyqtSignal(str)
    signal_show_badblocks_messagebox = QtCore.pyqtSignal(str)

    def __init__(self, main_window, parent=None):
        super(WorkerObject, self).__init__(parent)

        self.main_window = main_window
        self.signal_set_enabled.connect(self.main_window.set_enabled)
        self.signal_set_progress.connect(self.main_window.set_progress)
        self.signal_set_status.connect(self.main_window.set_status)
        self.signal_show_badblocks_messagebox.connect(self.main_window.show_badblocks_messagebox)

    @QtCore.pyqtSlot(str, str, str, str, int, int, str)
    def format(self, device, filesystem, partition_table, label, clustersize, badblocks_passes, badblocks_file):
        self.signal_set_enabled.emit(False)
        self.signal_set_progress.emit(0)

        # Unmount partitions before continuing.
        mount.unmount_all_partitions(device)

        self.signal_set_status.emit('Creating the partition table...')

        # Partition the usb drive.
        partitioning.create_partition_table(device, partition_table)

        if badblocks_passes > 0:
            self.signal_set_status.emit('Checking for bad blocks...')
            if clustersize == -1:
                formatting.check_badblocks(device, str(badblocks_passes), badblocks_file)
            else:
                formatting.check_badblocks(device, str(badblocks_passes), badblocks_file, str(clustersize))

            # Show message box informing the user of the badblocks check.
            self.signal_show_badblocks_messagebox.emit(badblocks_file)

        self.signal_set_progress.emit(25)
        self.signal_set_status.emit('Creating the partition...')

        partitioning.create_partition_wrapper(device, filesystem)

        if partition_table == 'gpt':
            partitioning.change_partition_name(device, label)

        self.signal_set_progress.emit(50)
        self.signal_set_status.emit('Creating the filesystem...')

        # Create the filesystem.
        if badblocks_passes > 0:
            formatting.create_filesystem(device, '1', filesystem, str(clustersize), label, badblocks_file)
        else:
            formatting.create_filesystem(device, '1', filesystem, str(clustersize), label)

        self.signal_set_progress.emit(100)
        self.signal_set_status.emit('Completed.')

        self.signal_set_enabled.emit(True)

    @QtCore.pyqtSlot(str, str, int, str)
    def make_bootable_dd(self, device, filename, badblocks_passes, badblocks_file):
        self.signal_set_enabled.emit(False)
        self.signal_set_progress.emit(0)

        # Unmount partitions before continuing.
        mount.unmount_all_partitions(device)

        if badblocks_passes > 0:
            self.signal_set_status.emit('Checking for bad blocks...')
            formatting.check_badblocks(device, str(badblocks_passes), badblocks_file)

            # Show message box informing the user of the badblocks check.
            self.signal_show_badblocks_messagebox.emit(badblocks_file)

        # Write image to usb
        self.signal_set_status.emit('Writing image...')
        dd.dd(filename, device)

        self.signal_set_progress.emit(100)
        self.signal_set_status.emit('Completed.')

        self.signal_set_enabled.emit(True)

    @QtCore.pyqtSlot(str, str, str, str, str, str, int, int, str, list, list, str)
    def make_bootable_iso(self, device, filename, filesystem, partition_table, target, label, clustersize,
                          badblocks_passes, badblocks_file, syslinux, syslinux_modules, grldr):
        self.signal_set_enabled.emit(False)
        self.signal_set_progress.emit(0)

        iso_mountpoint = '/tmp/usbmaker' + str(os.getpid()) + '-iso'
        mount.mount_iso(filename, iso_mountpoint)

        bootloader = [iso.get_uefi_bootloader_name(iso_mountpoint),
                      iso.get_bios_bootloader_name(iso_mountpoint)]

        # Check if a UEFI bootloader is present.
        if os.path.isfile(iso_mountpoint + '/boot/efi/bootx64.efi') or \
           os.path.isfile(iso_mountpoint + '/boot/efi/bootia32.efi'):
            uefi_bootloader_installed = True
        else:
            uefi_bootloader_installed = False

        mount.unmount(iso_mountpoint)

        # Ask user whether to replace the bootloader or use the included one.
        if uefi_bootloader_installed:
            if QtWidgets.QMessageBox.question(self.main_window, 'Replace UEFI bootloader?',
                                              'This ISO image already contains a UEFI bootloader.\n' +
                                              'Do you want to replace the UEFI bootloader?',
                                              QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                                              QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
                replace_uefi_bootloader = True
            else:
                replace_uefi_bootloader = False
        else:
            replace_uefi_bootloader = True

        # Change the target variable to preserve the UEFI bootloader.
        if not replace_uefi_bootloader:
            if target == 'uefi':
                target = 'none'
            else:
                target = 'bios'

        # Unmount partitions before continuing.
        mount.unmount_all_partitions(device)

        self.signal_set_status.emit('Creating the partition table...')

        # Partition the usb drive.
        partitioning.create_partition_table(device, partition_table)

        self.signal_set_status.emit('Creating the partition...')
        self.signal_set_progress.emit(5)

        partitioning.create_partition_wrapper(device, filesystem)

        if partition_table == 'gpt':
            partitioning.change_partition_name(device, label)

        if badblocks_passes > 0:
            self.signal_set_status.emit('Checking for bad blocks...')
            if clustersize == -1:
                formatting.check_badblocks(device, str(badblocks_passes), badblocks_file)
            else:
                formatting.check_badblocks(device, str(badblocks_passes), badblocks_file, str(clustersize))

            # Show message box informing the user of the badblocks check.
            self.signal_show_badblocks_messagebox.emit(badblocks_file)

        self.signal_set_status.emit('Creating the filesystem...')
        self.signal_set_progress.emit(10)

        # Create the filesystem.
        if badblocks_passes > 0:
            formatting.create_filesystem(device, '1', filesystem, str(clustersize), label, badblocks_file)
        else:
            formatting.create_filesystem(device, '1', filesystem, str(clustersize), label)

        self.signal_set_status.emit('Copying files...')
        self.signal_set_progress.emit(25)

        # Mount the usb and the iso file.
        usb_mountpoint = '/tmp/usbmaker' + str(os.getpid()) + '-usb'
        iso_mountpoint = '/tmp/usbmaker' + str(os.getpid()) + '-iso'
        mount.mount(device + '1', usb_mountpoint)
        mount.mount_iso(filename, iso_mountpoint)

        # Copy the iso contents to the usb drive.
        iso.copy_iso_contents(iso_mountpoint, usb_mountpoint)

        # Unmount the iso file.
        mount.unmount(iso_mountpoint)

        self.signal_set_status.emit('Installing the bootloader...')
        self.signal_set_progress.emit(80)

        # Make the usb bootable.
        iso.create_bootable_usb(device, usb_mountpoint, bootloader, target, partition_table,
                                syslinux, syslinux_modules, grldr)

        # Unmount the usb drive.
        mount.unmount(usb_mountpoint)

        if target == 'both':
            partitioning.mark_bootable(device, partition_table)

        self.signal_set_status.emit('Completed.')
        self.signal_set_progress.emit(100)

        self.signal_set_enabled.emit(True)

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()

window.show()
sys.exit(app.exec_())
