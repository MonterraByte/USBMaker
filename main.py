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
from PyQt5 import QtWidgets
from gui import Ui_MainWindow
import usb_info
import partitioning
import formatting
import dd
import mount
import iso


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setupUi(self)

        # Here we set up the gui elements that aren't modified
        # elsewhere in the code.
        self.pushButton_close.clicked.connect(self.close)

        self.comboBox_partscheme.insertItem(0, 'MBR partition scheme for BIOS or UEFI')
        self.comboBox_partscheme.insertItem(1, 'MBR partition scheme for UEFI')
        self.comboBox_partscheme.insertItem(2, 'GPT partition scheme for UEFI')

        self.comboBox_filesystem.insertItem(0, 'FAT32')
        self.comboBox_filesystem.insertItem(1, 'FAT16')
        self.comboBox_filesystem.insertItem(2, 'NTFS')
        self.comboBox_filesystem.insertItem(3, 'UDF')
        self.comboBox_filesystem.insertItem(4, 'exFAT')
        self.comboBox_filesystem.insertItem(5, 'ext4')
        self.comboBox_filesystem.insertItem(6, 'Btrfs')

        self.comboBox_checkbadblocks.insertItem(0, '1 Pass')
        self.comboBox_checkbadblocks.insertItem(1, '2 Passes')
        self.comboBox_checkbadblocks.insertItem(2, '3 Passes')
        self.comboBox_checkbadblocks.insertItem(3, '4 Passes')

        # Get the PID for this process
        self.pid = os.getpid()

        # Find syslinux
        if os.path.exists('/usr/lib/syslinux/bios/mbr.bin'):
            self.syslinux_mbr = '/usr/lib/syslinux/bios/mbr.bin'
        elif os.path.exists('/usr/lib/syslinux/mbr/mbr.bin'):
            self.syslinux_mbr = '/usr/lib/syslinux/mbr/mbr.bin'
        elif os.path.exists('/usr/share/syslinux/mbr.bin'):
            self.syslinux_mbr = '/usr/share/syslinux/mbr.bin'

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
        self.pushButton_start.clicked.connect(self.start)

    def update_gui(self):
        # This function is used to update/initialize the parts of the gui
        # that can be/are changed throughout the code.

        # Here the trigger for update_gui is disabled because otherwise
        # this function would trigger itself.
        self.comboBox_filesystem.currentIndexChanged.disconnect()
        self.comboBox_partscheme.currentIndexChanged.disconnect()
        self.comboBox_bootmethod.currentIndexChanged.disconnect()

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
            # The current index for the bootmethod comboBox is stored before
            # its update and restored afterwards.

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
                # checkBox_bootmethod are disabled.
                self.checkBox_bootmethod.setEnabled(False)
                self.comboBox_bootmethod.setEnabled(False)
            else:
                self.checkBox_bootmethod.setEnabled(True)
                self.comboBox_bootmethod.setEnabled(True)

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

    def refresh_device_list(self):
        self.device_id_list = usb_info.get_id_list()
        self.comboBox_device.clear()
        for device in self.device_id_list:
            self.comboBox_device.addItem('(' + str(round(usb_info.get_size(
                usb_info.get_block_device_name(device))/1073741824, 1)) + 'GiB) ' + device)

    def get_file_name(self):
        # getOpenFileName returns a tuple with the file path and the filter,
        # so to get only the file path we use [0].
        # If the user selects the cancel button, a empty string ('') is
        # written to self.filename.
        self.filename = QtWidgets.QFileDialog.getOpenFileName(directory=os.path.expanduser('~'),
                                                              filter='ISO Files (*.iso);;All Files (*)',
                                                              initialFilter='ISO Files (*.iso)')[0]
        default_label = ''
        isoinfo_output = subprocess.check_output(['isoinfo', '-d', '-i', self.filename]).decode()
        isoinfo_list = isoinfo_output.splitlines()
        for line in isoinfo_list:
            if re.search('Volume id:', line):
                default_label = line[11:]
        self.lineEdit_label.setText(default_label)

    def start(self):
        if self.comboBox_device.currentText() != '':
            if self.checkBox_bootmethod.isChecked():
                if self.filename != '':
                    if self.comboBox_bootmethod.currentText() == 'DD Image':
                        self.disable_gui()

                        self.progressBar.setValue(0)

                        # Collect information
                        device_id = self.device_id_list[self.comboBox_device.currentIndex()]
                        device = usb_info.get_block_device_name(device_id)

                        # Write image to usb
                        self.label_status.setText('Writing image...')
                        dd.dd(self.filename, device)

                        # Notify the kernel
                        partitioning.partprobe()

                        self.progressBar.setValue(100)
                        self.label_status.setText('Completed.')

                        self.enable_gui()
                    elif self.comboBox_bootmethod.currentText() == 'ISO Image':
                        self.disable_gui()

                        self.progressBar.setValue(0)

                        # Collect selected options.
                        label = self.lineEdit_label.text()
                        device_id = self.device_id_list[self.comboBox_device.currentIndex()]
                        if self.comboBox_partscheme.currentIndex() == 0 or self.comboBox_partscheme.currentIndex() == 1:
                            partition_table = 'msdos'
                        else:
                            partition_table = 'gpt'
                        filesystem = self.comboBox_filesystem.currentText().lower()

                        device = usb_info.get_block_device_name(device_id)

                        self.label_status.setText('Creating the partition table...')

                        # Partition the usb drive.
                        partitioning.create_partition_table(device, partition_table)

                        self.label_status.setText('Creating the partition...')
                        self.progressBar.setValue(5)

                        partitioning.create_partition_wrapper(device, filesystem)

                        self.label_status.setText('Creating the filesystem...')
                        self.progressBar.setValue(10)

                        # Create the filesystem.
                        formatting.create_filesystem(device + '1', filesystem, label)

                        # Inform the kernel of the partitioning change.
                        partitioning.partprobe()

                        self.label_status.setText('Copying files...')
                        self.progressBar.setValue(25)

                        # Mount the usb and the iso file.
                        usb_mountpoint = '/tmp/usbmaker' + str(self.pid) + '-usb'
                        iso_mountpoint = '/tmp/usbmaker' + str(self.pid) + '-iso'
                        mount.mount(device + '1', usb_mountpoint)
                        mount.mount_iso(self.filename, iso_mountpoint)

                        # Copy the iso contents to the usb drive.
                        iso.copy_iso_contents(iso_mountpoint, usb_mountpoint)

                        # Unmount the iso file.
                        mount.unmount(iso_mountpoint)

                        self.label_status.setText('Installing the bootloader...')
                        self.progressBar.setValue(80)

                        # Make the usb bootable.
                        if self.comboBox_partscheme.currentIndex() == 0:
                            target = 'bios'
                        else:
                            target = 'uefi'
                        iso.create_bootable_usb(device, usb_mountpoint, target, self.syslinux_mbr)

                        # Unmount the usb drive.
                        mount.unmount(usb_mountpoint)

                        if target == 'bios':
                            partitioning.mark_bootable(device)

                        self.label_status.setText('Completed.')
                        self.progressBar.setValue(100)

                        self.enable_gui()
                else:
                    self.label_status.setText('Error: No file selected.')
            else:
                self.disable_gui()

                self.progressBar.setValue(0)

                # Collect selected options.
                label = self.lineEdit_label.text()
                device_id = self.device_id_list[self.comboBox_device.currentIndex()]
                if self.comboBox_partscheme.currentIndex() == 0 or self.comboBox_partscheme.currentIndex() == 1:
                    partition_table = 'msdos'
                else:
                    partition_table = 'gpt'
                filesystem = self.comboBox_filesystem.currentText().lower()

                device = usb_info.get_block_device_name(device_id)

                self.label_status.setText('Creating the partition table...')

                # Partition the usb drive.
                partitioning.create_partition_table(device, partition_table)

                self.progressBar.setValue(25)
                self.label_status.setText('Creating the partition...')

                partitioning.create_partition_wrapper(device, filesystem)

                self.progressBar.setValue(50)
                self.label_status.setText('Creating the filesystem...')

                # Create the filesystem.
                formatting.create_filesystem(device + '1', filesystem, label)

                # Inform the kernel of the partitioning change.
                partitioning.partprobe()

                self.progressBar.setValue(100)
                self.label_status.setText('Completed.')

                self.enable_gui()
        else:
            self.label_status.setText('Error: no device selected.')


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()

window.show()
sys.exit(app.exec_())
