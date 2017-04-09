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

import os
import distutils.dir_util
import subprocess

# os.symlink raises a PermissionError when creating symlinks
# on filesystems that don't support them (FAT32, for example).
#
# This function is overriden so the program continues executing
# when this exception is raised. This is preferred to setting
# preserve_symlinks=0 in the distutils.dir_util.copy_tree function
# because it also avoids recursive symlinks.
orig_symlink = os.symlink


def _symlink(source, link_name, target_is_directory=False, dir_fd=None):
    try:
        orig_symlink(source, link_name, target_is_directory=target_is_directory, dir_fd=dir_fd)
    except PermissionError:
        pass

# Any function (distutils.dir_util.copy_tree in particular) that
# uses os.symlink will use the _symlink function instead.
os.symlink = _symlink


def copy_iso_contents(iso_mountpoint, device_mountpoint):
    distutils.dir_util.copy_tree(iso_mountpoint, device_mountpoint, preserve_symlinks=1)
    os.sync()


def create_bootable_usb(device, device_mountpoint, target='uefi', syslinux_mbr='/usr/lib/syslinux/bios/mbr.bin'):
    if target.lower() != 'uefi':
        if os.path.isdir(device_mountpoint + '/isolinux'):
            install_syslinux(device, device_mountpoint, syslinux_mbr)


def install_syslinux(device, device_mountpoint, syslinux_mbr):
    # Change the config files from ISOLINUX to SYSLINUX.
    if os.path.exists(device_mountpoint + '/isolinux') and not os.path.exists(device_mountpoint + '/syslinux'):
        os.rename(device_mountpoint + '/isolinux', device_mountpoint + '/syslinux')

    if os.path.exists(device_mountpoint + '/syslinux/isolinux.cfg') and not \
            os.path.exists(device_mountpoint + '/syslinux/syslinux.cfg'):
        os.rename(device_mountpoint + '/syslinux/isolinux.cfg', device_mountpoint + '/syslinux/syslinux.cfg')

    if os.path.exists(device_mountpoint + '/boot/isolinux') and not \
            os.path.exists(device_mountpoint + '/boot/syslinux'):
        os.rename(device_mountpoint + '/boot/isolinux', device_mountpoint + '/boot/syslinux')

    if os.path.exists(device_mountpoint + '/boot/syslinux/isolinux.cfg') and not \
            os.path.exists(device_mountpoint + '/boot/syslinux/syslinux.cfg'):
        os.rename(device_mountpoint + '/boot/syslinux/isolinux.cfg', device_mountpoint + '/boot/syslinux/syslinux.cfg')

    if os.path.exists(device_mountpoint + '/isolinux.cfg') and not os.path.exists(device_mountpoint + '/syslinux.cfg'):
        os.rename(device_mountpoint + '/isolinux.cfg', device_mountpoint + '/syslinux.cfg')

    # Install SYSLINUX to the partition.
    subprocess.run(['extlinux', '--install', device_mountpoint])

    # Install SYSLINUX to the MBR.
    subprocess.run(['dd', 'bs=440', 'count=1', 'if=' + syslinux_mbr, 'of=/dev/' + device])
