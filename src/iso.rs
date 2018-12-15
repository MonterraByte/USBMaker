//   Copyright © 2017-2018 Joaquim Monteiro
//
//   This file is part of USBMaker.
//
//   USBMaker is free software: you can redistribute it and/or modify
//   it under the terms of the GNU General Public License as published by
//   the Free Software Foundation, either version 3 of the License, or
//   (at your option) any later version.
//
//   USBMaker is distributed in the hope that it will be useful,
//   but WITHOUT ANY WARRANTY; without even the implied warranty of
//   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
//   GNU General Public License for more details.
//
//   You should have received a copy of the GNU General Public License
//   along with USBMaker.  If not, see <https://www.gnu.org/licenses/>.

use std::path::{Path, PathBuf};

use crate::copy;
use crate::error::IsoError;
use crate::formatting;
use crate::mount::Mount;
use crate::partitioning;
use crate::tui;

// TODO: bootloader install
pub fn create_bootable(
    device: &Path,
    iso: &Path,
    fs: &str,
    table: &str,
    label: Option<&str>,
    badblocks: bool,
    assume_yes: bool,
) -> Result<(), IsoError> {
    if !assume_yes {
        tui::warn(&*format!(
            "This will wipe all data on {}.",
            device.to_string_lossy()
        ));
        if !tui::prompt("Do you want to continue?", false) {
            return Err(IsoError::CanceledByUser);
        }
    }

    let partition_path: PathBuf = partitioning::create_table(device, table, true, true, None)
        .map_err(IsoError::PartitioningError)?;

    formatting::format(&partition_path, fs, badblocks, None, label, true)
        .map_err(IsoError::FormatError)?;

    let iso_mount: Mount = Mount::new(iso).map_err(IsoError::MountError)?;
    let device_mount: Mount = Mount::new(device).map_err(IsoError::MountError)?;

    copy::copy_dir_contents(iso_mount.path(), device_mount.path()).map_err(IsoError::CopyError)
}
