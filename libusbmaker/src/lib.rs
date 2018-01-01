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

//! The `libusbmaker` library contains tools for partitioning and formatting storage drives.
//!
//! It was created for the [USBMaker](https://github.com/gmes/USBMaker) project.

extern crate libparted_sys;
pub mod parted;

use std::path;
use std::fs;
use std::io;
use std::io::Write;

/// Copies the contents of one file to another.
///
/// # Errors
///
/// This function will return `Err` if:
///
/// - The destination file doesn't exist
///
/// - Opening the source file fails
///
/// - Opening the destination file fails
///
/// - Copying the contents of the reader to the writer fails
///
/// - Syncronizing the cached writes fails
///
/// # Examples
///
/// ```
/// use std::path::Path;
///
/// let source = Path::new("a.txt");
/// let destination = Path::new("b.txt");
/// dd(&source, &destination);
/// ```
pub fn dd(source: &path::Path, destination: &path::Path) -> Result<(), io::Error> {
    // Open the source file as read-only and create a BufReader for it
    let source_file: fs::File = fs::File::open(source)?;
    let mut reader: io::BufReader<fs::File> = io::BufReader::new(source_file);

    // Open the destination file as write-only and create a BufWriter for it
    let destination_file: fs::File = fs::OpenOptions::new().write(true).truncate(true).open(destination)?;
    let mut writer: io::BufWriter<fs::File> = io::BufWriter::new(destination_file);

    // Copiy the entire contents of the reader into the writer.
    io::copy(&mut reader, &mut writer)?;

    // Synchronize cached writes to persistent storage
    writer.flush()
}
