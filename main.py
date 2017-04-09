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
from PyQt5 import QtWidgets, QtCore
from gui import Ui_MainWindow
import about
import usb_info
import partitioning
import formatting
import dd
import mount
import iso


class StartRunnable(QtCore.QRunnable):
    def __init__(self, instance):
        QtCore.QRunnable.__init__(self)
        # self.instance should be the parent's self
        self.instance = instance

    def run(self):
        # Run self.start
        self.instance.start()


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
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
        self.messageBox_missingsyslinux = QtWidgets.QMessageBox()
        self.messageBox_missingsyslinux.setStandardButtons(QtWidgets.QMessageBox.Ok)

        self.messageBox_missingsyslinux.setWindowTitle('Syslinux is missing - USBMaker')
        self.messageBox_missingsyslinux\
            .setText('Syslinux was not found.\nThe creation of bootable drives with an ISO image may not work.')
        self.messageBox_missingsyslinux.setIcon(QtWidgets.QMessageBox.Warning)

        if os.path.exists('/usr/lib/syslinux/bios/mbr.bin'):
            self.syslinux_mbr = '/usr/lib/syslinux/bios/mbr.bin'
        elif os.path.exists('/usr/lib/syslinux/mbr/mbr.bin'):
            self.syslinux_mbr = '/usr/lib/syslinux/mbr/mbr.bin'
        elif os.path.exists('/usr/share/syslinux/mbr.bin'):
            self.syslinux_mbr = '/usr/share/syslinux/mbr.bin'
        else:
            self.syslinux_mbr = ''
            self.show_missingsyslinux_messagebox()

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

        # The start button is connected to the start function
        # through a QRunnable to make it execute on a separate thread.
        self.runnable = StartRunnable(self)
        self.runnable.setAutoDelete(False)
        self.pushButton_start.clicked.connect(self.thread_start)

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
                self.comboBox_bootmethod.insertItem(4, 'Syslinux 4')
                self.comboBox_bootmethod.insertItem(5, 'Syslinux 6')
                self.comboBox_bootmethod.insertItem(6, 'ReactOS')
                self.comboBox_bootmethod.insertItem(7, 'Grub 2')
                self.comboBox_bootmethod.insertItem(8, 'Grub4DOS')
            self.comboBox_bootmethod.setCurrentIndex(0)
            if bootmethod_current_index <= self.comboBox_bootmethod.count():
                # As the number of valid indexes may vary, the stored index is
                # only restored if it is valid. Otherwise it is set to 0.
                self.comboBox_bootmethod.setCurrentIndex(bootmethod_current_index)

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

    def show_about_window(self):
        center_point_x = int(self.x() + self.width() / 2)
        center_point_y = int(self.y() + self.height() / 2)
        x = int(center_point_x - self.about_window.width() / 2)
        y = int(center_point_y - self.about_window.height() / 2)
        self.about_window.move(x, y)
        self.about_window.show()

    def show_missingsyslinux_messagebox(self):
        center_point_x = int(self.x() + self.width() / 2)
        center_point_y = int(self.y() + self.height() / 2)
        # The message box needs to be shown in order for width() and height()
        # to return the correct values.
        self.messageBox_missingsyslinux.show()
        x = int(center_point_x - self.messageBox_missingsyslinux.width() / 2)
        y = int(center_point_y - self.messageBox_missingsyslinux.height() / 2)
        self.messageBox_missingsyslinux.move(x, y)

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

    def start(self):
        if self.comboBox_device.currentText() != '':
            # Collect information
            label = self.lineEdit_label.text()
            device_id = self.device_id_list[self.comboBox_device.currentIndex()]
            if self.comboBox_partscheme.currentIndex() == 0 or self.comboBox_partscheme.currentIndex() == 1:
                partition_table = 'msdos'
            else:
                partition_table = 'gpt'
            filesystem = self.comboBox_filesystem.currentText().lower()

            device = usb_info.get_block_device_name(device_id)

            if self.comboBox_partscheme.currentIndex() == 0:
                target = 'bios'
            else:
                target = 'uefi'

            if self.comboBox_checkbadblocks.currentIndex() == 1:
                num_passes = 2
            elif self.comboBox_checkbadblocks.currentIndex() == 2:
                num_passes = 3
            elif self.comboBox_checkbadblocks.currentIndex() == 3:
                num_passes = 4
            else:
                num_passes = 1

            badblocks_file = '/tmp/usbmaker' + str(self.pid) + '-badblocks.txt'

            # Cluster size
            if self.comboBox_clustersize.currentText() == '512':
                clustersize = '512'
            elif self.comboBox_clustersize.currentText() == '1024':
                clustersize = '1024'
            elif self.comboBox_clustersize.currentText() == '2048':
                clustersize = '2048'
            elif self.comboBox_clustersize.currentText() == '4096':
                clustersize = '4096'
            elif self.comboBox_clustersize.currentText() == '8192':
                clustersize = '8192'
            elif self.comboBox_clustersize.currentText() == '16384':
                clustersize = '16384'
            elif self.comboBox_clustersize.currentText() == '32768':
                clustersize = '32768'
            elif self.comboBox_clustersize.currentText() == '65536':
                clustersize = '65536'
            else:
                clustersize = ''

            if self.checkBox_bootmethod.isChecked():
                if self.filename != '':
                    if self.comboBox_bootmethod.currentText() == 'DD Image':
                        self.disable_gui()

                        self.progressBar.setValue(0)

                        # Unmount partitions before continuing.
                        mount.unmount_all_partitions(device)

                        if self.checkBox_checkbadblocks.isChecked():
                            self.label_status.setText('Checking for bad blocks...')
                            formatting.check_badblocks(device, num_passes, badblocks_file)

                            # Show message box informing the user of the badblocks check.
                            self.show_badblocks_messagebox(badblocks_file)

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

                        # Unmount partitions before continuing.
                        mount.unmount_all_partitions(device)

                        self.label_status.setText('Creating the partition table...')

                        # Partition the usb drive.
                        partitioning.create_partition_table(device, partition_table)

                        self.label_status.setText('Creating the partition...')
                        self.progressBar.setValue(5)

                        partitioning.create_partition_wrapper(device, filesystem)

                        if partition_table == 'gpt':
                            partitioning.change_partition_name(device, label)

                        # Inform the kernel of the partitioning change.
                        partitioning.partprobe()

                        if self.checkBox_checkbadblocks.isChecked():
                            self.label_status.setText('Checking for bad blocks...')
                            if clustersize == '':
                                formatting.check_badblocks(device, num_passes, badblocks_file)
                            else:
                                formatting.check_badblocks(device, num_passes, badblocks_file, clustersize)

                            # Show message box informing the user of the badblocks check.
                            self.show_badblocks_messagebox(badblocks_file)

                        self.label_status.setText('Creating the filesystem...')
                        self.progressBar.setValue(10)

                        # Create the filesystem.
                        if self.checkBox_checkbadblocks.isChecked():
                            formatting.create_filesystem(device + '1', filesystem, clustersize, label, badblocks_file)
                        else:
                            formatting.create_filesystem(device + '1', filesystem, clustersize, label)

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

                # Unmount partitions before continuing.
                mount.unmount_all_partitions(device)

                self.label_status.setText('Creating the partition table...')

                # Partition the usb drive.
                partitioning.create_partition_table(device, partition_table)

                if self.checkBox_checkbadblocks.isChecked():
                    self.label_status.setText('Checking for bad blocks...')
                    if clustersize == '':
                        formatting.check_badblocks(device, num_passes, badblocks_file)
                    else:
                        formatting.check_badblocks(device, num_passes, badblocks_file, clustersize)

                    # Show message box informing the user of the badblocks check.
                    self.show_badblocks_messagebox(badblocks_file)

                self.progressBar.setValue(25)
                self.label_status.setText('Creating the partition...')

                partitioning.create_partition_wrapper(device, filesystem)

                if partition_table == 'gpt':
                    partitioning.change_partition_name(device, label)

                # Inform the kernel of the partitioning change.
                partitioning.partprobe()

                self.progressBar.setValue(50)
                self.label_status.setText('Creating the filesystem...')

                # Create the filesystem.
                if self.checkBox_checkbadblocks.isChecked():
                    formatting.create_filesystem(device + '1', filesystem, clustersize, label, badblocks_file)
                else:
                    formatting.create_filesystem(device + '1', filesystem, clustersize, label)

                self.progressBar.setValue(100)
                self.label_status.setText('Completed.')

                self.enable_gui()
        else:
            self.label_status.setText('Error: no device selected.')

    def thread_start(self):
        # Start the self.start function in a different thread.
        # This is done to keep the main thread (the GUI) running.
        QtCore.QThreadPool.globalInstance().start(self.runnable)


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()

window.show()
sys.exit(app.exec_())
