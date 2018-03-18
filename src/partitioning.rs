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
use libparted::{Device, Disk, DiskType};

use error::PartitioningError;
use tui;

pub fn create_table(
    device_path: &Path,
    table_type_str: &str,
    assume_yes: bool,
) -> Result<(), PartitioningError> {
    let table_type: DiskType = match DiskType::get(table_type_str) {
        Some(table_type) => table_type,
        None => {
            return Err(PartitioningError::UnknownTableType(String::from(
                table_type_str,
            )))
        }
    };

    if !assume_yes {
        tui::warn("This will wipe all data on the target device.");
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

    let mut disk: Disk = match Disk::new_fresh(&mut device, table_type) {
        Ok(disk) => disk,
        Err(err) => return Err(PartitioningError::DiskOpenError(err)),
    };

    match disk.commit() {
        Ok(_) => {
            spinner.finish_with_message("Creating partition table... Done");
            Ok(())
        }
        Err(err) => Err(PartitioningError::CommitError(err)),
    }
}
