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
import shutil

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

# This makes any function (distutils.dir_util.copy_tree in particular)
# that uses os.symlink use the _symlink function instead:
# os.symlink = _symlink


def get_bios_bootloader_name(iso_mountpoint):
    if os.path.exists(iso_mountpoint + '/boot/isolinux') or os.path.exists(iso_mountpoint + '/boot/syslinux') or \
       os.path.exists(iso_mountpoint + '/syslinux') or os.path.exists(iso_mountpoint + '/isolinux') or \
       os.path.exists(iso_mountpoint + '/syslinux.cfg') or os.path.exists(iso_mountpoint + '/isolinux.cfg'):
        return 'syslinux'
    elif os.path.exists(iso_mountpoint + '/grub/grldr'):
        return 'grub4dos'
    else:
        return 'unknown'


def get_uefi_bootloader_name(iso_mountpoint):
    if os.path.exists(iso_mountpoint + '/boot/grub/grub.cfg') or \
            os.path.exists(iso_mountpoint + '/efi/boot/grub.cfg'):
        return 'grub2'
    elif os.path.exists(iso_mountpoint + '/loader/loader.conf'):
        return 'systemd-boot'
    else:
        return 'unknown'


def copy_iso_contents(iso_mountpoint, device_mountpoint):
    os.symlink = _symlink
    distutils.dir_util.copy_tree(iso_mountpoint, device_mountpoint, preserve_symlinks=1)
    os.sync()


def create_bootable_usb(device, device_mountpoint, bootloader, target, partition_table, syslinux):
    if bootloader[0].lower() == 'syslinux' or bootloader[1].lower() == 'syslinux':
        isolinux_to_syslinux(device_mountpoint)
    if target.lower() == 'both':
        if bootloader[0].lower() == 'syslinux':
            install_syslinux(device, device_mountpoint, 'uefi', partition_table, syslinux)
        if bootloader[1].lower() == 'syslinux':
            install_syslinux(device, device_mountpoint, 'bios', partition_table, syslinux)
    elif target.lower() == 'bios':
        if bootloader[1].lower() == 'syslinux':
            install_syslinux(device, device_mountpoint, 'bios', partition_table, syslinux)
    elif target.lower() == 'uefi':
        if bootloader[0].lower() == 'syslinux':
            install_syslinux(device, device_mountpoint, 'uefi', partition_table, syslinux)


def install_syslinux(device, device_mountpoint, target, partition_table, syslinux):
    if target == 'bios':
        # Install SYSLINUX to the partition.
        subprocess.run(['extlinux', '--install', device_mountpoint])

        # Install SYSLINUX to the MBR.
        if partition_table == 'gpt':
            subprocess.run(['dd', 'bs=440', 'count=1', 'if=' + syslinux[0] + '/gptmbr.bin', 'of=/dev/' + device])
        else:
            subprocess.run(['dd', 'bs=440', 'count=1', 'if=' + syslinux[0] + '/mbr.bin', 'of=/dev/' + device])
    elif target == 'uefi':
        # Create directories if they are not present.
        if not os.path.isdir(device_mountpoint + '/efi'):
            os.makedirs(device_mountpoint + '/efi')

        if not os.path.isdir(device_mountpoint + '/efi/boot'):
            os.makedirs(device_mountpoint + '/efi/boot')

        # Copy the UEFI bootloader.
        shutil.copy(syslinux[1] + '/syslinux.efi', device_mountpoint + '/efi/boot/bootx64.efi')
        shutil.copy(syslinux[2] + '/syslinux.efi', device_mountpoint + '/efi/boot/bootia32.efi')

        shutil.copy(syslinux[1] + '/ldlinux.e64', device_mountpoint + '/efi/boot/ldlinux.e64')
        shutil.copy(syslinux[2] + '/ldlinux.e32', device_mountpoint + '/efi/boot/ldlinux.e32')

        # Copy the modules.
        if not os.path.isdir(device_mountpoint + '/efi/boot/efi64'):
            os.makedirs(device_mountpoint + '/efi/boot/efi64')

        if not os.path.isdir(device_mountpoint + '/efi/boot/efi32'):
            os.makedirs(device_mountpoint + '/efi/boot/efi32')

        for file in os.listdir(syslinux[1]):
            if file[-4:] == '.c32':
                shutil.copy(syslinux[1] + '/' + file, device_mountpoint + '/efi/boot/efi64/' + file)

        for file in os.listdir(syslinux[2]):
            if file[-4:] == '.c32':
                shutil.copy(syslinux[2] + '/' + file, device_mountpoint + '/efi/boot/efi32/' + file)

        # Create the config file.
        if not os.path.exists(device_mountpoint + '/efi/boot/syslinux.cfg'):
            if os.path.exists(device_mountpoint + '/boot/syslinux/syslinux.cfg'):
                # /boot/syslinux/syslinux.cfg
                with open(device_mountpoint + '/efi/boot/syslinux.cfg', mode='w', encoding='utf_8', newline='\n') as \
                        syslinux_conf:
                    syslinux_conf.write('PATH ./efi64\nINCLUDE /boot/syslinux/syslinux.cfg\n')

            elif os.path.exists(device_mountpoint + '/syslinux/syslinux.cfg'):
                # /syslinux/syslinux.cfg
                with open(device_mountpoint + '/efi/boot/syslinux.cfg', mode='w', encoding='utf_8', newline='\n') as \
                        syslinux_conf:
                    syslinux_conf.write('PATH ./efi64\nINCLUDE /syslinux/syslinux.cfg\n')

            elif os.path.exists(device_mountpoint + '/syslinux.cfg'):
                # /syslinux.cfg
                with open(device_mountpoint + '/efi/boot/syslinux.cfg', mode='w', encoding='utf_8', newline='\n') as \
                        syslinux_conf:
                    syslinux_conf.write('PATH ./efi64\nINCLUDE /syslinux.cfg\n')
            created_new_conf = True
        else:
            created_new_conf = False

        # Config file for x64 (Syslinux 6.04+).
        if not os.path.exists(device_mountpoint + '/efi/boot/syslx64.cfg'):
            # /efi/boot/syslinux.cfg
            if not created_new_conf:
                # Use original config file.
                with open(device_mountpoint + '/efi/boot/syslx64.cfg', mode='w', encoding='utf_8', newline='\n') as \
                        syslinux_conf:
                    syslinux_conf.write('PATH ./efi64\nINCLUDE /efi/boot/syslinux.cfg\n')

            # /boot/syslinux/syslinux.cfg
            elif os.path.exists(device_mountpoint + '/boot/syslinux/syslinux.cfg'):
                with open(device_mountpoint + '/efi/boot/syslx64.cfg', mode='w', encoding='utf_8', newline='\n') as \
                        syslinux_conf:
                    syslinux_conf.write('PATH ./efi64\nINCLUDE /boot/syslinux/syslinux.cfg\n')

            # /syslinux/syslinux.cfg
            elif os.path.exists(device_mountpoint + '/syslinux/syslinux.cfg'):
                with open(device_mountpoint + '/efi/boot/syslx64.cfg', mode='w', encoding='utf_8', newline='\n') as \
                        syslinux_conf:
                    syslinux_conf.write('PATH ./efi64\nINCLUDE /syslinux/syslinux.cfg\n')

            # /syslinux.cfg
            elif os.path.exists(device_mountpoint + '/syslinux.cfg'):
                with open(device_mountpoint + '/efi/boot/syslx64.cfg', mode='w', encoding='utf_8', newline='\n') as \
                        syslinux_conf:
                    syslinux_conf.write('PATH ./efi64\nINCLUDE /syslinux.cfg\n')

        if not os.path.exists(device_mountpoint + '/efi/boot/syslia32.cfg'):
            # /efi/boot/syslinux.cfg
            if not created_new_conf:
                # Use original config file.
                with open(device_mountpoint + '/efi/boot/syslia32.cfg', mode='w', encoding='utf_8', newline='\n') as \
                        syslinux_conf:
                    syslinux_conf.write('PATH ./efi32\nINCLUDE /efi/boot/syslinux.cfg\n')

            # /boot/syslinux/syslinux.cfg
            elif os.path.exists(device_mountpoint + '/boot/syslinux/syslinux.cfg'):
                with open(device_mountpoint + '/efi/boot/syslia32.cfg', mode='w', encoding='utf_8', newline='\n') as \
                        syslinux_conf:
                    syslinux_conf.write('PATH ./efi32\nINCLUDE /boot/syslinux/syslinux.cfg\n')

            # /syslinux/syslinux.cfg
            elif os.path.exists(device_mountpoint + '/syslinux/syslinux.cfg'):
                with open(device_mountpoint + '/efi/boot/syslia32.cfg', mode='w', encoding='utf_8', newline='\n') as \
                        syslinux_conf:
                    syslinux_conf.write('PATH ./efi32\nINCLUDE /syslinux/syslinux.cfg\n')

            # /syslinux.cfg
            elif os.path.exists(device_mountpoint + '/syslinux.cfg'):
                with open(device_mountpoint + '/efi/boot/syslia32.cfg', mode='w', encoding='utf_8', newline='\n') as \
                        syslinux_conf:
                    syslinux_conf.write('PATH ./efi32\nINCLUDE /syslinux.cfg\n')


def isolinux_to_syslinux(device_mountpoint):
    # Change the config files from ISOLINUX to SYSLINUX.
    # SYSLINUX searches for its config file in "/boot/syslinux", "/syslinux" and "/",
    # by this order.
    # The only config file changed should be the first one detected,
    # in order to reduce the modifications made to the iso file's content.

    # /boot/syslinux
    if os.path.exists(device_mountpoint + '/boot/isolinux') and not \
            os.path.exists(device_mountpoint + '/boot/syslinux'):
        os.rename(device_mountpoint + '/boot/isolinux', device_mountpoint + '/boot/syslinux')

    if os.path.exists(device_mountpoint + '/boot/syslinux/isolinux.cfg') and not \
            os.path.exists(device_mountpoint + '/boot/syslinux/syslinux.cfg'):
        os.rename(device_mountpoint + '/boot/syslinux/isolinux.cfg', device_mountpoint + '/boot/syslinux/syslinux.cfg')

    # /syslinux
    if not os.path.exists(device_mountpoint + '/boot/syslinux/syslinux.cfg'):
        if os.path.exists(device_mountpoint + '/isolinux') and not os.path.exists(device_mountpoint + '/syslinux'):
            os.rename(device_mountpoint + '/isolinux', device_mountpoint + '/syslinux')

        if os.path.exists(device_mountpoint + '/syslinux/isolinux.cfg') and not \
                os.path.exists(device_mountpoint + '/syslinux/syslinux.cfg'):
            os.rename(device_mountpoint + '/syslinux/isolinux.cfg', device_mountpoint + '/syslinux/syslinux.cfg')

        # /
        if not os.path.exists(device_mountpoint + '/syslinux/syslinux.cfg'):
            if os.path.exists(device_mountpoint + '/isolinux.cfg') and \
                    not os.path.exists(device_mountpoint + '/syslinux.cfg'):
                os.rename(device_mountpoint + '/isolinux.cfg', device_mountpoint + '/syslinux.cfg')
