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

use std::fs::remove_dir;
use std::path::{Path, PathBuf};
use std::process::Command;

use tempfile::{Builder, TempDir};

use error::MountError;

pub struct Mount {
    mountpoint: PathBuf,
}

impl Mount {
    pub fn new(source: &Path) -> Result<Mount, MountError> {
        let mountpoint: TempDir = match Builder::new().prefix("usbmaker").tempdir() {
            Ok(dir) => dir,
            Err(err) => return Err(MountError::TempdirCreationError(err)),
        };

        match Command::new("mount")
            .arg("-r")
            .arg(source)
            .arg(mountpoint.path())
            .status()
        {
            Ok(status) => if !status.success() {
                return Err(MountError::CommandFailed(status.code()));
            },
            Err(err) => return Err(MountError::CommandExecError(err)),
        };

        // If everything succeeded, comsume the TempDir as we want to remove it manually.
        Ok(Mount {
            mountpoint: mountpoint.into_path(),
        })
    }

    pub fn path(&self) -> &Path {
        &self.mountpoint
    }
}

impl Drop for Mount {
    fn drop(&mut self) {
        // Remove the empty mountpoint only if unmounting succeeds.
        // Otherwise, it should be deleted on shutdown by the OS, as it's
        // located in the system's temporary directory.
        if let Ok(status) = Command::new("umount").arg(&self.mountpoint).status() {
            if status.success() {
                let _ = remove_dir(&self.mountpoint);
            }
        }
    }
}
