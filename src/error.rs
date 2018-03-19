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

pub enum PartitioningError {
    CanceledByUser,
    CommitError(io::Error),
    ConstraintError,
    DeviceOpenError(io::Error),
    DiskOpenError(io::Error),
    PartitionAddError(io::Error),
    PartitionCreateError(io::Error),
    UnknownTableType(String),
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

impl USBMakerError for PartitioningError {
    fn error_code(&self) -> i32 {
        match self {
            &PartitioningError::CanceledByUser => 1,
            &PartitioningError::CommitError(_) => 8,
            &PartitioningError::ConstraintError => 9,
            &PartitioningError::DeviceOpenError(_) => 10,
            &PartitioningError::DiskOpenError(_) => 11,
            &PartitioningError::PartitionAddError(_) => 12,
            &PartitioningError::PartitionCreateError(_) => 13,
            &PartitioningError::UnknownTableType(_) => 14,
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

impl fmt::Display for PartitioningError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            &PartitioningError::CanceledByUser => {
                write!(f, "The operation was canceled by the user")
            }
            &PartitioningError::CommitError(ref e) => {
                write!(f, "Failed to commit changes to disk: {}", e.description())
            }
            &PartitioningError::ConstraintError => write!(f, "Failed to get the constraint"),
            &PartitioningError::DeviceOpenError(ref e) => {
                write!(f, "Failed open the target device: {}", e.description())
            }
            &PartitioningError::DiskOpenError(ref e) => {
                write!(f, "Failed open the partition table: {}", e.description())
            }
            &PartitioningError::PartitionAddError(ref e) => write!(
                f,
                "Failed to add partition to partition table: {}",
                e.description()
            ),
            &PartitioningError::PartitionCreateError(ref e) => {
                write!(f, "Failed create partition in memory: {}", e.description())
            }
            &PartitioningError::UnknownTableType(ref s) => {
                write!(f, "Unknown partition table type: {}", s)
            }
        }
    }
}
