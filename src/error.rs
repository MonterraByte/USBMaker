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

use std::error::Error;
use std::fmt;
use std::io;

pub trait USBMakerError: fmt::Display {
    fn error_code(&self) -> i32;
}

pub enum DdError {
    CanceledByUser,
    InputFileMetadataError(io::Error),
    InputFileOpenError(io::Error),
    OutputFileOpenError(io::Error),
    ReadError(io::Error),
    SyncError(io::Error),
    WriteError(io::Error),
}

impl USBMakerError for DdError {
    fn error_code(&self) -> i32 {
        match self {
            &DdError::CanceledByUser => 1,
            &DdError::InputFileMetadataError(_) => 2,
            &DdError::InputFileOpenError(_) => 3,
            &DdError::OutputFileOpenError(_) => 4,
            &DdError::ReadError(_) => 5,
            &DdError::SyncError(_) => 6,
            &DdError::WriteError(_) => 7,
        }
    }
}

impl fmt::Display for DdError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            &DdError::CanceledByUser => write!(f, "The operation was canceled by the user"),
            &DdError::InputFileMetadataError(ref e) => write!(
                f,
                "Failed to get the input file's metadata: {}",
                e.description()
            ),
            &DdError::InputFileOpenError(ref e) => {
                write!(f, "Failed open the input file: {}", e.description())
            }
            &DdError::OutputFileOpenError(ref e) => {
                write!(f, "Failed open the output file: {}", e.description())
            }
            &DdError::ReadError(ref e) => {
                write!(f, "Failed to read from the input file: {}", e.description())
            }
            &DdError::SyncError(ref e) => {
                write!(f, "Failed to sync changes to disk: {}", e.description())
            }
            &DdError::WriteError(ref e) => {
                write!(f, "Failed to write to the output file: {}", e.description())
            }
        }
    }
}
