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


def create_gpt_table(device):
    subprocess.run(['parted', '-s', '"/dev/' + device + '"', 'mktable', 'gpt'])


def create_msdos_table(device):
    subprocess.run(['parted', '-s', '"/dev/' + device + '"', 'mktable', 'msdos'])


def create_partition(device, fs_type='ext2'):
    subprocess.run(['parted', '-s', '"/dev/' + device + '"', 'mkpart', 'primary', fs_type, '1MiB', '100%'])
