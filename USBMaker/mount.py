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

import os
import subprocess
import usb_info


def mount(partition, mountpoint):
    os.makedirs(mountpoint)
    subprocess.run(['mount', '/dev/' + partition, mountpoint])


def mount_iso(iso, mountpoint):
    os.makedirs(mountpoint)
    subprocess.run(['mount', '-o', 'loop,ro', iso, mountpoint])


def unmount(mountpoint):
    subprocess.run(['umount', mountpoint])
    # The mount point should be empty, so we can use rmdir.
    os.rmdir(mountpoint)


def unmount_partition(partition):
    subprocess.run(['umount', '/dev/' + partition])


def unmount_all_partitions(device):
    partitions = usb_info.get_partitions(device)
    for partition in partitions:
        unmount_partition(partition)
