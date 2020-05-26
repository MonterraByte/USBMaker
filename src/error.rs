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

use std::error::Error;
use std::fmt;
use std::io;

#[derive(Debug)]
pub enum USBMakerError {
    CommandFailed(Option<i32>, String),
    CommandLaunchFailed(io::Error, String),
    IoError(io::Error, String),
    PartitioningError(io::Error, String),
}

impl USBMakerError {
    pub fn error_code(&self) -> i32 {
        match self {
            USBMakerError::CommandFailed(_, _) => 1,
            USBMakerError::CommandLaunchFailed(_, _) => 2,
            USBMakerError::IoError(_, _) => 3,
            USBMakerError::PartitioningError(_, _) => 4,
        }
    }
}

impl fmt::Display for USBMakerError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            USBMakerError::CommandFailed(exit, c) => match exit {
                Some(code) => write!(f, "{} exited with code {}", c, code),
                None => write!(f, "{} was terminated by a signal", c),
            },
            USBMakerError::CommandLaunchFailed(err, c) => {
                write!(f, "Failed to lauch command {}: {}", c, err)
            }
            USBMakerError::IoError(err, step) => write!(f, "I/O error while {}: {}", step, err),
            USBMakerError::PartitioningError(err, step) => {
                write!(f, "Error preparing partition table ({}): {}", step, err)
            }
        }
    }
}

impl Error for USBMakerError {}
