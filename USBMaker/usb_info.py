#   Copyright © 2017-2020 Joaquim Monteiro
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
import re
from pathlib import Path


def get_id_list():
    return [device.name
            for device in Path('/dev/disk/by-id/').iterdir()
            if device.name.startswith('usb-') and not re.search('-part', device.name)]


def get_size(device_id):
    # Convert device ID to the respective sd* name, as /sys/block/ only contains symlinks for
    # these names
    device = os.path.basename(os.readlink('/dev/disk/by-id/' + device_id))

    # /sys/block/*/size is read to get the number of sectors in the usb.
    with open('/sys/block/' + device + '/size', mode='r') as size_file:
        sectors = int(size_file.read().rstrip())

    # /sys/block/*/queue/logical_block_size is read to get the size of sectors in the usb.
    with open('/sys/block/' + device + '/queue/logical_block_size', mode='r') as block_size_file:
        block_size = int(block_size_file.read().rstrip())

    # The sector size is multiplied by the number of sectors to get the number of bytes.
    return sectors * block_size
