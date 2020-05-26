//   Copyright © 2017-2020 Joaquim Monteiro
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

use std::ffi::OsStr;
use std::fmt;
use std::path::Path;
use std::process::Command;
use std::str;

use indicatif::{ProgressBar, ProgressDrawTarget};

use crate::error::USBMakerError;

macro_rules! os {
    ($s:tt) => {
        std::ffi::OsStr::new($s)
    };
}

#[derive(Clone, Copy, Debug)]
pub enum FileSystem {
    Btrfs,
    Exfat,
    Ext2,
    Ext3,
    Ext4,
    F2fs,
    Fat32,
    Ntfs,
    Udf,
    Xfs,
}

#[derive(Debug)]
pub struct FileSystemParseError;

impl fmt::Display for FileSystemParseError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "unknown filesystem")
    }
}

impl str::FromStr for FileSystem {
    type Err = FileSystemParseError;
    fn from_str(s: &str) -> Result<Self, Self::Err> {
        match s {
            "btrfs" => Ok(FileSystem::Btrfs),
            "exfat" => Ok(FileSystem::Exfat),
            "ext2" => Ok(FileSystem::Ext2),
            "ext3" => Ok(FileSystem::Ext3),
            "ext4" => Ok(FileSystem::Ext4),
            "f2fs" => Ok(FileSystem::F2fs),
            "fat32" => Ok(FileSystem::Fat32),
            "ntfs" => Ok(FileSystem::Ntfs),
            "udf" => Ok(FileSystem::Udf),
            "xfs" => Ok(FileSystem::Xfs),
            _ => Err(FileSystemParseError),
        }
    }
}

fn get_format_command(
    fs: FileSystem,
    partition: &Path,
    label: Option<&str>,
    check_badblocks: bool,
) -> Command {
    let executable = match fs {
        FileSystem::Btrfs => os!("mkfs.btrfs"),
        FileSystem::Exfat => os!("mkfs.exfat"),
        FileSystem::Ext2 => os!("mkfs.ext2"),
        FileSystem::Ext3 => os!("mkfs.ext3"),
        FileSystem::Ext4 => os!("mkfs.ext4"),
        FileSystem::F2fs => os!("mkfs.f2fs"),
        FileSystem::Fat32 => os!("mkfs.fat"),
        FileSystem::Ntfs => os!("mkfs.ntfs"),
        FileSystem::Udf => os!("mkfs.udf"),
        FileSystem::Xfs => os!("mkfs.xfs"),
    };

    let mut args: Vec<&OsStr> = match fs {
        FileSystem::Fat32 => vec![os!("-F32")],
        FileSystem::Ntfs => {
            if !check_badblocks {
                vec![os!("-Q")]
            } else {
                Vec::new()
            }
        }
        _ => Vec::new(),
    };

    if check_badblocks {
        match fs {
            FileSystem::Ext2 | FileSystem::Ext3 | FileSystem::Ext4 | FileSystem::Fat32 => {
                args.push(os!("-c"))
            }
            _ => (),
        }
    }

    if let Some(label) = label {
        args.push(match fs {
            FileSystem::Btrfs
            | FileSystem::Ext2
            | FileSystem::Ext3
            | FileSystem::Ext4
            | FileSystem::Ntfs
            | FileSystem::Xfs => os!("-L"),
            FileSystem::Exfat | FileSystem::Fat32 => os!("-n"),
            FileSystem::F2fs | FileSystem::Udf => os!("-l"),
        });
        args.push(OsStr::new(label));
    }

    args.push(partition.as_os_str());

    let mut command = Command::new(executable);
    command.args(&args);
    command
}

pub fn format(
    partition: &Path,
    fs: FileSystem,
    label: Option<&str>,
    check_badblocks: bool,
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

    let mut command: Command = get_format_command(fs, partition, label, check_badblocks);

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
