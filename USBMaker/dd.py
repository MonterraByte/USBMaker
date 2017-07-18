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
import hashlib
import os


def dd(iso, device):
    subprocess.run(['dd', 'if=' + iso, 'of=/dev/' + device])


def dd_check(iso, device):
    subprocess.run(['dd', 'if=/dev/' + device, 'of=/tmp/usbmaker_image_' + device + '.iso',
                    'count=' + str(os.path.getsize(iso)/512)])
    dd_hash = hashlib.sha512()
    dd_iso = open('/tmp/usbmaker_image_' + device + '.iso', 'rb')
    dd_iso_buffer = dd_iso.read(2**23)
    while len(dd_iso_buffer) > 0:
        dd_hash.update(dd_iso_buffer)
        dd_iso_buffer = dd_iso.read(2**23)
    dd_iso_hash = dd_hash.hexdigest()
    os.remove('/tmp/usbmaker_image_' + device + '.iso')

    iso_hash = hashlib.sha512()
    orig_iso = open(iso, 'rb')
    orig_iso_buffer = orig_iso.read(2**23)
    while len(orig_iso_buffer) > 0:
        iso_hash.update(orig_iso_buffer)
        orig_iso_buffer = orig_iso.read(2**23)
    orig_iso_hash = iso_hash.hexdigest()

    if dd_iso_hash == orig_iso_hash:
        return True
    else:
        return False
