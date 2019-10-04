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

use std::path::{Path, PathBuf};
use std::process::Command;

use indicatif::{ProgressBar, ProgressDrawTarget};
use libparted::FileSystemType;

use crate::error::USBMakerError;
use crate::partitioning;
use crate::tui;

pub fn format(
    path: &Path,
    fs: &str,
    badblocks: bool,
    is_device: Option<&str>,
    label: Option<&str>,
    assume_yes: bool,
) -> Result<(), USBMakerError> {
    if !assume_yes {
        tui::warn(&*format!(
            "This will wipe all data on {}.",
            path.to_string_lossy()
        ));
        if !tui::prompt("Do you want to continue?", false) {
            return Err(USBMakerError::CanceledByUser);
        }
    }

    let partition: PathBuf = if is_device.is_some() {
        let fs_type: Option<FileSystemType> = match fs {
            "exfat" | "udf" => FileSystemType::get("ntfs"),
            "f2fs" => FileSystemType::get("ext4"),
            _ => FileSystemType::get(fs),
        };

        partitioning::create_table(path, is_device.unwrap(), true, true, fs_type)?
    } else {
        path.to_path_buf()
    };

    create_filesystem(&partition, fs, label, badblocks)
}

macro_rules! get_command {
    ( $executable:expr, $( $arg:expr ),* ) => {
        {
            let mut command = Command::new($executable);
            $(
                command.arg($arg);
            )*
            command
        }
    };
}

fn create_filesystem(
    partition: &Path,
    fs: &str,
    label: Option<&str>,
    badblocks: bool,
) -> Result<(), USBMakerError> {
    let spinner: ProgressBar = ProgressBar::new_spinner();
    spinner.set_draw_target(ProgressDrawTarget::stderr());
    spinner.set_message("Creating filesystem...");
    spinner.enable_steady_tick(100);

    match Command::new("wipefs")
        .arg("-af")
        .arg(partition.as_os_str())
        .status()
    {
        Ok(status) => {
            if !status.success() {
                return Err(USBMakerError::CommandFailed(
                    status.code(),
                    format!("wipefs -af {}", partition.display()),
                ));
            }
        }
        Err(err) => {
            return Err(USBMakerError::CommandLaunchFailed(
                err,
                format!("wipefs -af {}", partition.display()),
            ))
        }
    }

    let mut command: Command = match (fs, label, badblocks) {
        ("btrfs", None, _) => get_command!("mkfs.btrfs", partition.as_os_str()),
        ("btrfs", Some(lbl), _) => get_command!("mkfs.btrfs", "-L", lbl, partition.as_os_str()),
        ("exfat", None, _) => get_command!("mkfs.exfat", partition.as_os_str()),
        ("exfat", Some(lbl), _) => get_command!("mkfs.exfat", "-n", lbl, partition.as_os_str()),
        ("ext2", None, false) => get_command!("mkfs.ext2", partition.as_os_str()),
        ("ext2", Some(lbl), false) => get_command!("mkfs.ext2", "-L", lbl, partition.as_os_str()),
        ("ext2", None, true) => get_command!("mkfs.ext2", "-c", partition.as_os_str()),
        ("ext2", Some(lbl), true) => {
            get_command!("mkfs.ext2", "-c", "-L", lbl, partition.as_os_str())
        }
        ("ext3", None, false) => get_command!("mkfs.ext3", partition.as_os_str()),
        ("ext3", Some(lbl), false) => get_command!("mkfs.ext3", "-L", lbl, partition.as_os_str()),
        ("ext3", None, true) => get_command!("mkfs.ext3", "-c", partition.as_os_str()),
        ("ext3", Some(lbl), true) => {
            get_command!("mkfs.ext3", "-c", "-L", lbl, partition.as_os_str())
        }
        ("ext4", None, false) => get_command!("mkfs.ext4", partition.as_os_str()),
        ("ext4", Some(lbl), false) => get_command!("mkfs.ext4", "-L", lbl, partition.as_os_str()),
        ("ext4", None, true) => get_command!("mkfs.ext4", "-c", partition.as_os_str()),
        ("ext4", Some(lbl), true) => {
            get_command!("mkfs.ext4", "-c", "-L", lbl, partition.as_os_str())
        }
        ("f2fs", None, _) => get_command!("mkfs.f2fs", partition.as_os_str()),
        ("f2fs", Some(lbl), _) => get_command!("mkfs.f2fs", "-l", lbl, partition.as_os_str()),
        ("fat32", None, false) => get_command!("mkfs.fat", "-F32", partition.as_os_str()),
        ("fat32", Some(lbl), false) => {
            get_command!("mkfs.fat", "-F32", "-n", lbl, partition.as_os_str())
        }
        ("fat32", None, true) => get_command!("mkfs.fat", "-F32", "-c", partition.as_os_str()),
        ("fat32", Some(lbl), true) => {
            get_command!("mkfs.fat", "-F32", "-c", "-n", lbl, partition.as_os_str())
        }
        ("ntfs", None, false) => get_command!("mkfs.ntfs", "-Q", partition.as_os_str()),
        ("ntfs", Some(lbl), false) => {
            get_command!("mkfs.ntfs", "-Q", "-L", lbl, partition.as_os_str())
        }
        ("ntfs", None, true) => get_command!("mkfs.ntfs", partition.as_os_str()),
        ("ntfs", Some(lbl), true) => get_command!("mkfs.ntfs", "-L", lbl, partition.as_os_str()),
        ("udf", None, _) => get_command!("mkfs.udf", partition.as_os_str()),
        ("udf", Some(lbl), _) => get_command!("mkfs.udf", "-l", lbl, partition.as_os_str()),
        ("xfs", None, _) => get_command!("mkfs.xfs", partition.as_os_str()),
        ("xfs", Some(lbl), _) => get_command!("mkfs.xfs", "-L", lbl, partition.as_os_str()),
        _ => panic!("Unknown filesystem: {}", fs.to_owned()),
    };

    match command.status() {
        Ok(status) => {
            if status.success() {
                spinner.finish_with_message("Filesystem created successfully");
                Ok(())
            } else {
                Err(USBMakerError::CommandFailed(
                    status.code(),
                    format!("{:?}", command),
                ))
            }
        }
        Err(err) => Err(USBMakerError::CommandLaunchFailed(
            err,
            format!("{:?}", command),
        )),
    }
}
