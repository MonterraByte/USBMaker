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

use std::fs::{self, DirEntry, Metadata};
use std::io;
use std::os;
use std::path::{Path, PathBuf};

/// Copies the contents of a directory to another directory.
pub fn copy_dir_contents<P: AsRef<Path>>(source: P, destination: P) -> io::Result<()> {
    for entry in fs::read_dir(source)? {
        let entry: DirEntry = entry?;
        let metadata: Metadata = entry.metadata()?;
        let dest_path: PathBuf = destination.as_ref().join(entry.file_name());

        if metadata.is_file() {
            fs::copy(entry.path(), dest_path)?;
        } else if metadata.is_dir() {
            if !dest_path.exists() {
                fs::create_dir(&dest_path)?;
            }
            copy_dir_contents(entry.path(), dest_path)?;
        } else if metadata.file_type().is_symlink() {
            let symlink_target: PathBuf = fs::read_link(entry.path())?;
            if let Err(err) = os::unix::fs::symlink(&symlink_target, &dest_path) {
                if err.kind() == io::ErrorKind::PermissionDenied {
                    // Filesystem doesn't support symlinks
                    // so let's copy the actual files
                    let actual_metadata: Metadata = entry.path().metadata()?;
                    if actual_metadata.is_file() {
                        fs::copy(entry.path(), &dest_path)?;
                    } else {
                        if !dest_path.exists() {
                            fs::create_dir(&dest_path)?;
                        }
                        copy_dir_contents(entry.path(), dest_path)?;
                    }
                } else {
                    return Err(err);
                }
            };
        }
    }
    Ok(())
}
