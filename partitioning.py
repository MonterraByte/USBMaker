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

import subprocess
import usb_info


def create_partition_table(device, table):
    if table.lower() == 'msdos' or table.lower() == 'mbr':
        subprocess.run(['parted', '-s', '/dev/' + device, 'mktable', 'msdos'])
    elif table.lower() == 'gpt':
        subprocess.run(['parted', '-s', '/dev/' + device, 'mktable', 'gpt'])


def create_partition(device, fs_type='ext2'):
    subprocess.run(['parted', '-s', '/dev/' + device, 'mkpart', 'primary', fs_type, '1MiB', '100%'])


def create_custom_sized_partition(device, size, fs_type='ext2'):
    subprocess.run(['parted', '-s', '/dev/' + device, 'mkpart', 'primary', fs_type, '1MiB', size])


def create_partition_wrapper(device, fs_type):
    if fs_type.lower() == 'fat32':
        create_partition(device, 'fat32')
    elif fs_type.lower() == 'fat16':
        if usb_info.get_size(device) > 4294967296:
            create_custom_sized_partition(device, '4096MiB', 'fat16')
        else:
            create_partition(device, 'fat16')
    elif fs_type.lower() == 'ntfs':
        create_partition(device, 'ntfs')
    elif fs_type.lower() == 'exfat':
        # exFAT and NTFS share the same fs-type
        create_partition(device, 'ntfs')
    elif fs_type.lower() == 'ext4':
        create_partition(device, 'ext4')
    elif fs_type.lower() == 'btrfs':
        create_partition(device, 'btrfs')
    else:
        create_partition(device)


def mark_bootable(device):
    subprocess.run(['parted', '-s', '/dev/' + device, 'set', '1', 'boot', 'on'])


def partprobe():
    # Informs the kernel of changes in the partition table.
    subprocess.run(['partprobe'])
