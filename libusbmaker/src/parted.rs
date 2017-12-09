//   Copyright © 2017 Joaquim Monteiro
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

//! This module contains partitioning functionality built upon `libparted`.

use std::fmt;
use std::error;
use std::ffi::{CStr, CString};
use std::os::raw::c_int;
use libparted_sys::{ped_constraint_destroy, ped_constraint_exact, ped_device_destroy,
                    ped_device_get, ped_device_sync, ped_disk_add_partition, ped_disk_commit,
                    ped_disk_destroy, ped_disk_new, ped_disk_new_fresh, ped_disk_probe,
                    ped_disk_type_get, ped_file_system_type_get, ped_geometry_destroy,
                    ped_geometry_new, ped_geometry_set_end, ped_partition_destroy,
                    ped_partition_new, PedConstraint, PedDevice, PedDisk, PedDiskType,
                    PedFileSystemType, PedGeometry, PedPartition, PedSector, _PedPartitionType};


/// The `DiskType` type. Contains all the supported partition tables.
pub enum DiskType {
    GPT,
    MSDOS,
}

impl DiskType {
    fn cstr(&self) -> &CStr {
        match self {
            &DiskType::GPT => CStr::from_bytes_with_nul(b"gpt\0").unwrap(),
            &DiskType::MSDOS => CStr::from_bytes_with_nul(b"msdos\0").unwrap(),
        }
    }
}

/// The `FileSystemType` type. Contains all the partition types supported by Parted.
///
/// When creating a partition, its partition type is stored in the partition table.
/// The partition type stored changes depending on the `FileSystemType` used.
pub enum FileSystemType {
    Btrfs,
    Ext2,
    Ext3,
    Ext4,
    Fat16,
    Fat32,
    Hfs,
    HfsPlus,
    Hfsx,
    HpUfs,
    Jfs,
    LinuxSwapV0,
    LinuxSwapV1,
    Nilfs2,
    Ntfs,
    Reiserfs,
    SunUfs,
    Swsusp,
    Xfs,
}

impl FileSystemType {
    fn cstr(&self) -> &CStr {
        match self {
            &FileSystemType::Btrfs => CStr::from_bytes_with_nul(b"btrfs\0").unwrap(),
            &FileSystemType::Ext2 => CStr::from_bytes_with_nul(b"ext2\0").unwrap(),
            &FileSystemType::Ext3 => CStr::from_bytes_with_nul(b"ext3\0").unwrap(),
            &FileSystemType::Ext4 => CStr::from_bytes_with_nul(b"ext4\0").unwrap(),
            &FileSystemType::Fat16 => CStr::from_bytes_with_nul(b"fat16\0").unwrap(),
            &FileSystemType::Fat32 => CStr::from_bytes_with_nul(b"fat32\0").unwrap(),
            &FileSystemType::Hfs => CStr::from_bytes_with_nul(b"hfs\0").unwrap(),
            &FileSystemType::HfsPlus => CStr::from_bytes_with_nul(b"hfs+\0").unwrap(),
            &FileSystemType::Hfsx => CStr::from_bytes_with_nul(b"hfsx\0").unwrap(),
            &FileSystemType::HpUfs => CStr::from_bytes_with_nul(b"hp-ufs\0").unwrap(),
            &FileSystemType::Jfs => CStr::from_bytes_with_nul(b"jfs\0").unwrap(),
            &FileSystemType::LinuxSwapV0 => CStr::from_bytes_with_nul(b"linux-swap(v0)\0").unwrap(),
            &FileSystemType::LinuxSwapV1 => CStr::from_bytes_with_nul(b"linux-swap(v1)\0").unwrap(),
            &FileSystemType::Nilfs2 => CStr::from_bytes_with_nul(b"nilfs2\0").unwrap(),
            &FileSystemType::Ntfs => CStr::from_bytes_with_nul(b"ntfs\0").unwrap(),
            &FileSystemType::Reiserfs => CStr::from_bytes_with_nul(b"reiserfs\0").unwrap(),
            &FileSystemType::SunUfs => CStr::from_bytes_with_nul(b"sun-ufs\0").unwrap(),
            &FileSystemType::Swsusp => CStr::from_bytes_with_nul(b"swsusp\0").unwrap(),
            &FileSystemType::Xfs => CStr::from_bytes_with_nul(b"xfs\0").unwrap(),
        }
    }
}

/// Creates an empty partition table.
///
/// # Errors
///
/// This function will return a `PartedError` if it fails to create the partition table.
///
/// # Examples
///
/// ```
/// let device: CString = CString::new("/dev/sdb").unwrap();
/// create_label(&device, DiskType::GPT);
/// ```
pub fn create_label(device: &CString, disk_type: DiskType) -> Result<c_int, PartedError> {
    let ped_device: *mut PedDevice = unsafe { ped_device_get(device.as_ptr()) };
    if ped_device.is_null() {
        return Err(PartedError::NullPedDevice);
    }

    let ped_disk_type: *mut PedDiskType =
        unsafe { ped_disk_type_get(disk_type.cstr().as_ptr()) };
    if ped_disk_type.is_null() {
        unsafe { ped_device_destroy(ped_device) };
        return Err(PartedError::NullPedDiskType);
    }

    let ped_disk: *mut PedDisk = unsafe { ped_disk_new_fresh(ped_device, ped_disk_type) };
    if ped_disk.is_null() {
        unsafe { ped_device_destroy(ped_device) };
        return Err(PartedError::NullPedDisk);
    }

    let result: c_int = unsafe { ped_disk_commit(ped_disk) };

    unsafe {
        ped_disk_destroy(ped_disk);
        ped_device_destroy(ped_device);
    }

    if result == 0 {
        Err(PartedError::CommitFail)
    } else {
        Ok(result)
    }
}

/// Creates a partition inside an empty partition table.
/// The created partition occupies the whole drive.
///
/// # Errors
///
/// This function will return a `PartedError` if it fails to create the partition.
///
/// # Examples
///
/// ```
/// let device: CString = CString::new("/dev/sdb").unwrap();
/// create_partition(&device, FileSystemType::Fat32);
/// ```
pub fn create_partition(device: &CString, fs_type: FileSystemType) -> Result<c_int, PartedError> {
    let ped_device: *mut PedDevice = unsafe { ped_device_get(device.as_ptr()) };
    if ped_device.is_null() {
        return Err(PartedError::NullPedDevice);
    }

    let disk_type: DiskType = match probe_table(ped_device) {
        Ok(disk_type) => disk_type,
        Err(table) => {
            unsafe { ped_device_destroy(ped_device) };
            return Err(PartedError::UnknownPartitionTable(table));
        }
    };

    // Start at 1 MiB (== 1048576 Bytes) for optimal performance
    // This should be fine for most drives, including Advanced Format (4k sector size) drives
    let start: PedSector = unsafe { 1048576 / (*ped_device).sector_size };
    let end: PedSector = match disk_type {
        DiskType::GPT => unsafe {
            (*ped_device).length - (1048576 / (*ped_device).sector_size) - 1
        },
        DiskType::MSDOS => unsafe { (*ped_device).length - 1 },
    };

    let ped_disk: *mut PedDisk = unsafe { ped_disk_new(ped_device) };
    if ped_disk.is_null() {
        unsafe { ped_device_destroy(ped_device) };
        return Err(PartedError::NullPedDisk);
    }

    let ped_file_system_type: *const PedFileSystemType =
        unsafe { ped_file_system_type_get(fs_type.cstr().as_ptr()) };
    if ped_file_system_type.is_null() {
        unsafe {
            ped_disk_destroy(ped_disk);
            ped_device_destroy(ped_device);
        }
        return Err(PartedError::NullPedFileSystemType);
    }

    let ped_partition: *mut PedPartition = unsafe {
        ped_partition_new(
            ped_disk,
            _PedPartitionType::PED_PARTITION_NORMAL,
            ped_file_system_type,
            start,
            end,
        )
    };
    if ped_partition.is_null() {
        unsafe {
            ped_disk_destroy(ped_disk);
            ped_device_destroy(ped_device);
        }
        return Err(PartedError::NullPedPartition);
    }

    let ped_geometry: *mut PedGeometry = unsafe { ped_geometry_new(ped_device, start, 1) };
    if ped_geometry.is_null() {
        unsafe {
            ped_partition_destroy(ped_partition);
            ped_disk_destroy(ped_disk);
            ped_device_destroy(ped_device);
        }
        return Err(PartedError::NullPedGeometry);
    }
    unsafe { ped_geometry_set_end(ped_geometry, end) };

    let ped_constraint: *mut PedConstraint = unsafe { ped_constraint_exact(ped_geometry) };
    if ped_constraint.is_null() {
        unsafe {
            ped_geometry_destroy(ped_geometry);
            ped_partition_destroy(ped_partition);
            ped_disk_destroy(ped_disk);
            ped_device_destroy(ped_device);
        }
        return Err(PartedError::NullPedConstraint);
    }

    if unsafe { ped_disk_add_partition(ped_disk, ped_partition, ped_constraint) } == 0 {
        unsafe {
            ped_constraint_destroy(ped_constraint);
            ped_geometry_destroy(ped_geometry);
            ped_partition_destroy(ped_partition);
            ped_disk_destroy(ped_disk);
            ped_device_destroy(ped_device);
        }
        return Err(PartedError::AddPartitionFail);
    }

    let result: c_int = unsafe { ped_disk_commit(ped_disk) };

    unsafe {
        ped_constraint_destroy(ped_constraint);
        ped_geometry_destroy(ped_geometry);
        ped_partition_destroy(ped_partition);
        ped_disk_destroy(ped_disk);
        ped_device_destroy(ped_device);
    }

    if result == 0 {
        Err(PartedError::CommitFail)
    } else {
        Ok(result)
    }
}

/// Synchronizes cached writes to persistent storage.
///
/// # Errors
///
/// This function will return a `PartedError` if it fails to sync the write cache.
///
/// # Examples
///
/// ```
/// let device: CString = CString::new("/dev/sdb").unwrap();
/// sync(&device);
/// ```
pub fn sync(device: &CString) -> Result<c_int, PartedError> {
    let ped_device: *mut PedDevice = unsafe { ped_device_get(device.as_ptr()) };
    if ped_device.is_null() {
        return Err(PartedError::NullPedDevice);
    }

    let result: c_int = unsafe { ped_device_sync(ped_device) };

    unsafe { ped_device_destroy(ped_device) };

    if result == 0 {
        Err(PartedError::SyncFail)
    } else {
        Ok(result)
    }
}

fn probe_table(ped_device: *mut PedDevice) -> Result<DiskType, String> {
    let disk_type: *const PedDiskType = unsafe { ped_disk_probe(ped_device) };
    let disk_type_cstr: &CStr = unsafe { CStr::from_ptr((*disk_type).name) };

    if disk_type_cstr == DiskType::GPT.cstr() {
        Ok(DiskType::GPT)
    } else if disk_type_cstr == DiskType::MSDOS.cstr() {
        Ok(DiskType::MSDOS)
    } else {
        Err(disk_type_cstr.to_string_lossy().to_string())
    }
}

/// Custom error type used in this module.
#[derive(Debug)]
pub enum PartedError {
    NullPedDevice,
    NullPedDiskType,
    NullPedDisk,
    NullPedFileSystemType,
    NullPedPartition,
    NullPedGeometry,
    NullPedConstraint,
    CommitFail,
    AddPartitionFail,
    SyncFail,
    UnknownPartitionTable(String),
}

impl fmt::Display for PartedError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            &PartedError::NullPedDevice => write!(f, "Libparted returned a null PedDevice"),
            &PartedError::NullPedDiskType => write!(f, "Libparted returned a null PedDiskType"),
            &PartedError::NullPedDisk => write!(f, "Libparted returned a null PedDisk"),
            &PartedError::NullPedFileSystemType => {
                write!(f, "Libparted returned a null NullPedFileSystemType")
            }
            &PartedError::NullPedPartition => {
                write!(f, "Libparted returned a null NullPedPartition")
            }
            &PartedError::NullPedGeometry => write!(f, "Libparted returned a null NullPedGeometry"),
            &PartedError::NullPedConstraint => {
                write!(f, "Libparted returned a null NullPedConstraint")
            }
            &PartedError::CommitFail => write!(f, "Libparted failed to commit the changes"),
            &PartedError::AddPartitionFail => write!(f, "Libparted failed to add the partition"),
            &PartedError::SyncFail => write!(f, "Libparted failed to flush the write cache"),
            &PartedError::UnknownPartitionTable(ref table) => {
                write!(f, "Unknown partition table: {}", table)
            }
        }
    }
}

impl error::Error for PartedError {
    fn description(&self) -> &str {
        match self {
            &PartedError::NullPedDevice => "Libparted returned a null PedDevice",
            &PartedError::NullPedDiskType => "Libparted returned a null PedDiskType",
            &PartedError::NullPedDisk => "Libparted returned a null PedDisk",
            &PartedError::NullPedFileSystemType => {
                "Libparted returned a null NullPedFileSystemType"
            }
            &PartedError::NullPedPartition => "Libparted returned a null NullPedPartition",
            &PartedError::NullPedGeometry => "Libparted returned a null NullPedGeometry",
            &PartedError::NullPedConstraint => "Libparted returned a null NullPedConstraint",
            &PartedError::CommitFail => "Libparted failed to commit the changes",
            &PartedError::AddPartitionFail => "Libparted failed to add the partition",
            &PartedError::SyncFail => "Libparted failed to flush the write cache",
            &PartedError::UnknownPartitionTable(ref _table) => "Unknown partition table",
        }
    }
}
