USBMaker
========

Features
--------

* Format USB storage devices to FAT32, FAT16, NTFS, UDF, exFAT, ext4 and Btrfs.
* Create MBR (MS-DOS) or GPT partition tables.
* Create bootable drives for BIOS and UEFI.

Requirements
------------

* [Python 3](https://python.org)
* [PyQt5](https://www.riverbankcomputing.com/software/pyqt/intro)

The following are not required to execute USBMaker, but are needed for some of its functionality:

* [parted](https://www.gnu.org/software/parted/parted.html)
* [dd](https://www.gnu.org/software/coreutils/coreutils.html)
* [badblocks](http://e2fsprogs.sourceforge.net/)
* [isoinfo](http://cdrtools.sourceforge.net/)
* [mkfs.fat](https://github.com/dosfstools/dosfstools)
* [mkfs.exfat](https://github.com/relan/exfat)
* [mkfs.ntfs](https://www.tuxera.com/community/open-source-ntfs-3g/)
* [mkfs.udf](https://github.com/pali/udftools)
* [mkfs.ext4](http://e2fsprogs.sourceforge.net/)
* [mkfs.btrfs](https://btrfs.wiki.kernel.org/)
* [GRUB 2](https://www.gnu.org/software/grub/)
* [SYSLINUX](http://www.syslinux.org/)
* [GRUB4DOS](https://github.com/chenall/grub4dos)
* [systemd-boot](https://www.freedesktop.org/wiki/Software/systemd/systemd-boot/)


Installing
----------

USBMaker can be used without installation (by executing `main.py`). However, a `setup.py` is included to allow installation.

To install USBMaker using `setup.py`:

    <Python 3 executable> setup.py install

Note that using your package manager is preferred to installing directly with `setup.py`.

---

Copyright © 2017 Joaquim Monteiro

USBMaker is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

USBMaker is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with USBMaker.  If not, see <https://www.gnu.org/licenses/>.
