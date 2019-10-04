//   Copyright © 2017-2019 Joaquim Monteiro
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

use std::io;
use std::path::{Path, PathBuf};

use indicatif::{ProgressBar, ProgressDrawTarget};
use libparted::{Constraint, Device, Disk, DiskType, FileSystemType, Partition, PartitionType};

use crate::error::USBMakerError;
use crate::tui;

pub fn create_table(
    device_path: &Path,
    table_type_str: &str,
    assume_yes: bool,
    partition: bool,
    fs_type: Option<FileSystemType>,
) -> Result<PathBuf, USBMakerError> {
    let table_type: DiskType = DiskType::get(table_type_str).expect("Unknown partition table");

    if !assume_yes {
        tui::warn(&*format!(
            "This will wipe all data on {}.",
            device_path.to_string_lossy()
        ));
        if !tui::prompt("Do you want to continue?", false) {
            return Err(USBMakerError::CanceledByUser);
        }
    }

    let mut return_path: PathBuf = device_path.to_path_buf();

    let spinner: ProgressBar = ProgressBar::new_spinner();
    spinner.set_draw_target(ProgressDrawTarget::stderr());
    spinner.set_message("Creating partition table...");
    spinner.enable_steady_tick(100);

    let mut device: Device = Device::get(device_path)
        .map_err(|e| USBMakerError::IoError(e, String::from("opening device for partitioning")))?;

    let length: i64 = device.length() as i64;
    let sector_size: i64 = device.sector_size() as i64;

    let mut disk: Disk = Disk::new_fresh(&mut device, table_type)
        .map_err(|e| USBMakerError::IoError(e, String::from("opening disk for partitioning")))?;
    if partition {
        let mebibyte: i64 = 1048576 / sector_size;

        let end: i64 = match table_type_str {
            "gpt" => length - mebibyte - 1,
            _ => length - 1,
        };
        let mut partition: Partition = Partition::new(
            &disk,
            PartitionType::PED_PARTITION_NORMAL,
            fs_type.as_ref(),
            mebibyte,
            end,
        )
        .map_err(|e| USBMakerError::PartitioningError(e, String::from("creating partition")))?;

        let constraint: Constraint = disk.constraint_any().ok_or_else(|| {
            USBMakerError::PartitioningError(
                io::Error::new(io::ErrorKind::Other, ""),
                String::from("generating constraint"),
            )
        })?;

        disk.add_partition(&mut partition, &constraint)
            .map_err(|e| USBMakerError::PartitioningError(e, String::from("adding partition")))?;

        if let Some(path) = partition.get_path() {
            return_path = path.to_path_buf();
        }
    }

    match disk.commit() {
        Ok(_) => {
            spinner.finish_with_message("Creating partition table... Done");
            Ok(return_path)
        }
        Err(err) => Err(USBMakerError::IoError(
            err,
            String::from("commiting partition table to disk"),
        )),
    }
}
