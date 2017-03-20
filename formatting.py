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


def create_fat32_filesystem(partition, label='', badblocks_file='', clustersize=0):
    if clustersize == 0:
        if label == '':
            if badblocks_file == '':
                subprocess.run(['mkfs.fat', '-F32', '/dev/' + partition])
            else:
                subprocess.run(['mkfs.fat', '-F32', '-l', badblocks_file, '/dev/' + partition])
        else:
            if badblocks_file == '':
                subprocess.run(['mkfs.fat', '-F32', '-n', label.upper(), '/dev/' + partition])
            else:
                subprocess.run(['mkfs.fat', '-F32', '-n', label.upper(), '-l', badblocks_file, '/dev/' + partition])
    else:
        if label == '':
            if badblocks_file == '':
                subprocess.run(['mkfs.fat', '-F32', '-S', clustersize, '/dev/' + partition])
            else:
                subprocess.run(['mkfs.fat', '-F32', '-S', clustersize, '-l', badblocks_file, '/dev/' + partition])
        else:
            if badblocks_file == '':
                subprocess.run(['mkfs.fat', '-F32', '-n', label.upper(), '-S', clustersize, '/dev/' + partition])
            else:
                subprocess.run(['mkfs.fat', '-F32', '-n', label.upper(), '-S', clustersize, '-l', badblocks_file,
                                '/dev/' + partition])


def create_fat16_filesystem(partition, label='', badblocks_file='', clustersize=0):
    if clustersize == 0:
        if label == '':
            if badblocks_file == '':
                subprocess.run(['mkfs.fat', '-F16', '/dev/' + partition])
            else:
                subprocess.run(['mkfs.fat', '-F16', '-l', badblocks_file, '/dev/' + partition])
        else:
            if badblocks_file == '':
                subprocess.run(['mkfs.fat', '-F16', '-n', label.upper(), '/dev/' + partition])
            else:
                subprocess.run(['mkfs.fat', '-F16', '-n', label.upper(), '-l', badblocks_file, '/dev/' + partition])
    else:
        if label == '':
            if badblocks_file == '':
                subprocess.run(['mkfs.fat', '-F16', '-S', clustersize, '/dev/' + partition])
            else:
                subprocess.run(['mkfs.fat', '-F16', '-S', clustersize, '-l', badblocks_file, '/dev/' + partition])
        else:
            if badblocks_file == '':
                subprocess.run(['mkfs.fat', '-F16', '-n', label.upper(), '-S', clustersize, '/dev/' + partition])
            else:
                subprocess.run(['mkfs.fat', '-F16', '-n', label.upper(), '-S', clustersize, '-l', badblocks_file,
                                '/dev/' + partition])


def create_exfat_filesystem(partition, label=''):
    if label == '':
        subprocess.run(['mkfs.exfat', '/dev/' + partition])
    else:
        subprocess.run(['mkfs.exfat', '-n', label[:15], '/dev/' + partition])


def create_ntfs_filesystem(partition, label='', clustersize=0):
    if clustersize == 0:
        if label == '':
            subprocess.run(['mkfs.ntfs', '-Q', '/dev/' + partition])
        else:
            subprocess.run(['mkfs.ntfs', '-Q', '-L', label, '/dev/' + partition])
    else:
        if label == '':
            subprocess.run(['mkfs.ntfs', '-Q', '-c', clustersize, '/dev/' + partition])
        else:
            subprocess.run(['mkfs.ntfs', '-Q', '-L', label, '-c', clustersize, '/dev/' + partition])


def create_udf_filesystem(partition, label='', clustersize=0):
    if clustersize == 0:
        subprocess.run(['mkfs.udf', '-l', label, '/dev/' + partition])
    else:
        subprocess.run(['mkfs.udf', '-l', label, '-b', clustersize, '/dev/' + partition])


def create_ext4_filesystem(partition, label='', badblocks_file='', clustersize=0):
    if clustersize == 0:
        if label == '':
            if badblocks_file == '':
                subprocess.run(['mkfs.ext4', '/dev/' + partition])
            else:
                subprocess.run(['mkfs.ext4', '-l', badblocks_file, '/dev/' + partition])
        else:
            if badblocks_file == '':
                subprocess.run(['mkfs.ext4', '-L', label, '/dev/' + partition])
            else:
                subprocess.run(['mkfs.ext4', '-L', label, '-l', badblocks_file, '/dev/' + partition])
    else:
        if label == '':
            if badblocks_file == '':
                subprocess.run(['mkfs.ext4', '-b', clustersize, '/dev/' + partition])
            else:
                subprocess.run(['mkfs.ext4', '-b', clustersize, '-l', badblocks_file, '/dev/' + partition])
        else:
            if badblocks_file == '':
                subprocess.run(['mkfs.ext4', '-L', label, '-b', clustersize, '/dev/' + partition])
            else:
                subprocess.run(['mkfs.ext4', '-L', label, '-b', clustersize, '-l', badblocks_file, '/dev/' + partition])


def create_btrfs_filesystem(partition, label='', badblocks_file='', clustersize=0):
    if clustersize == 0:
        if label == '':
            if badblocks_file == '':
                subprocess.run(['mkfs.btrfs', '/dev/' + partition])
            else:
                subprocess.run(['mkfs.btrfs', '-l', badblocks_file, '/dev/' + partition])
        else:
            if badblocks_file == '':
                subprocess.run(['mkfs.btrfs', '-L', label, '/dev/' + partition])
            else:
                subprocess.run(['mkfs.btrfs', '-L', label, '-l', badblocks_file, '/dev/' + partition])
    else:
        if label == '':
            if badblocks_file == '':
                subprocess.run(['mkfs.btrfs', '-n', clustersize, '/dev/' + partition])
            else:
                subprocess.run(['mkfs.btrfs', '-n', clustersize, '-l', badblocks_file, '/dev/' + partition])
        else:
            if badblocks_file == '':
                subprocess.run(['mkfs.btrfs', '-L', label, '-n', clustersize, '/dev/' + partition])
            else:
                subprocess.run(['mkfs.btrfs', '-L', label, '-n', clustersize, '-l', badblocks_file, '/dev/' + partition])


def create_filesystem(partition, filesystem, clustersize, label='', badblocks_file=''):
    if filesystem.lower() == 'fat32':
        create_fat32_filesystem(partition, label, badblocks_file, clustersize)
    elif filesystem.lower() == 'fat16':
        create_fat16_filesystem(partition, label, badblocks_file, clustersize)
    elif filesystem.lower() == 'ntfs':
        create_ntfs_filesystem(partition, label, clustersize)
    elif filesystem.lower() == 'exfat':
        create_exfat_filesystem(partition, label)
    elif filesystem.lower() == 'ext4':
        create_ext4_filesystem(partition, label, badblocks_file, clustersize)
    elif filesystem.lower() == 'btrfs':
        create_btrfs_filesystem(partition, label, badblocks_file, clustersize)
    elif filesystem.lower() == 'udf':
        create_udf_filesystem(partition, label, clustersize)


def check_badblocks(partition, num_passes, badblocks_file, clustersize=1024):
    subprocess.run(['badblocks', '-w', '-p', num_passes, '-b', clustersize, '-o', badblocks_file, '/dev/' + partition])
