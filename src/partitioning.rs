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

use std::path::Path;

use indicatif::{ProgressBar, ProgressDrawTarget};
use libparted::{Constraint, Device, Disk, DiskType, Partition, PartitionType};

use error::PartitioningError;
use tui;

pub fn create_table(
    device_path: &Path,
    table_type_str: &str,
    assume_yes: bool,
    partition: bool,
) -> Result<(), PartitioningError> {
    let table_type: DiskType = match DiskType::get(table_type_str) {
        Some(table_type) => table_type,
        None => {
            return Err(PartitioningError::UnknownTableType(
                table_type_str.to_owned(),
            ))
        }
    };

    if !assume_yes {
        tui::warn(&*format!(
            "This will wipe all data on {}.",
            device_path.to_string_lossy()
        ));
        match tui::prompt(&*format!("Do you want to continue?"), false) {
            true => (),
            false => return Err(PartitioningError::CanceledByUser),
        }
    }

    let spinner: ProgressBar = ProgressBar::new_spinner();
    spinner.set_draw_target(ProgressDrawTarget::stderr());
    spinner.set_message("Creating partition table...");
    spinner.enable_steady_tick(100);

    let mut device: Device = match Device::get(device_path) {
        Ok(device) => device,
        Err(err) => return Err(PartitioningError::DeviceOpenError(err)),
    };

    let length: i64 = device.length() as i64;
    let sector_size: i64 = device.sector_size() as i64;

    let mut disk: Disk = match Disk::new_fresh(&mut device, table_type) {
        Ok(disk) => disk,
        Err(err) => return Err(PartitioningError::DiskOpenError(err)),
    };

    if partition {
        let mebibyte: i64 = 1048576 / sector_size;

        let end: i64 = match table_type_str {
            "gpt" => length - mebibyte - 1,
            _ => length - 1,
        };
        let mut partition: Partition = match Partition::new(
            &disk,
            PartitionType::PED_PARTITION_NORMAL,
            None,
            mebibyte,
            end,
        ) {
            Ok(partition) => partition,
            Err(err) => return Err(PartitioningError::PartitionCreateError(err)),
        };

        let constraint: Constraint = match disk.constraint_any() {
            Some(constraint) => constraint,
            None => return Err(PartitioningError::ConstraintError),
        };

        match disk.add_partition(&mut partition, &constraint) {
            Ok(_) => (),
            Err(err) => return Err(PartitioningError::PartitionAddError(err)),
        };
    }

    match disk.commit() {
        Ok(_) => {
            spinner.finish_with_message("Creating partition table... Done");
            Ok(())
        }
        Err(err) => Err(PartitioningError::CommitError(err)),
    }
}
