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


def create_fat32_filesystem(partition, label=''):
    if label != '':
        subprocess.run(['mkfs.fat', '-F32', '-n', '"' + label + '"', '"/dev/' + partition + '"'])
    else:
        subprocess.run(['mkfs.fat', '-F32', '"/dev/' + partition + '"'])


def create_fat16_filesystem(partition, label=''):
    if label != '':
        subprocess.run(['mkfs.fat', '-F16', '-n', '"' + label + '"', '"/dev/' + partition + '"'])
    else:
        subprocess.run(['mkfs.fat', '-F16', '"/dev/' + partition + '"'])


def create_exfat_filesystem(partition, label=''):
    if label != '':
        subprocess.run(['mkfs.exfat', '-n', '"' + label[:15] + '"', '"/dev/' + partition + '"'])
    else:
        subprocess.run(['mkfs.exfat', '"/dev/' + partition + '"'])


def create_ntfs_filesystem(partition, label=''):
    if label != '':
        subprocess.run(['mkfs.ntfs', '-Q', '-L', '"' + label + '"', '"/dev/' + partition + '"'])
    else:
        subprocess.run(['mkfs.ntfs', '-Q', '"/dev/' + partition + '"'])


def create_udf_filesystem(partition, label=''):
    subprocess.run(['mkfs.udf', '-l', '"' + label + '"', '"/dev/' + partition + '"'])


def create_ext4_filesystem(partition, label=''):
    if label != '':
        subprocess.run(['mkfs.ext4', '-L', '"' + label + '"', '"/dev/' + partition + '"'])
    else:
        subprocess.run(['mkfs.ext4', '"/dev/' + partition + '"'])
