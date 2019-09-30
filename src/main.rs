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

extern crate ansi_term;
#[macro_use]
extern crate clap;
extern crate indicatif;
extern crate libparted;
extern crate tempfile;

mod copy;
mod error;
mod formatting;
mod iso;
mod mount;
mod partitioning;
mod tui;

use std::path::PathBuf;
use std::process;

use ansi_term::Colour;
use clap::{App, Arg};

fn main() {
    let matches = App::new("USBMaker")
        .author(crate_authors!())
        .version(crate_version!())
        .about("Create bootable usb drives")
        .args(&[
            Arg::with_name("device")
                .takes_value(true)
                .required(true)
                .index(1)
                .help("Device to make bootable"),
            Arg::with_name("iso")
                .takes_value(true)
                .required(true)
                .help("ISO file to use as source"),
            Arg::with_name("badblocks")
                .short("b")
                .long("badblocks")
                .takes_value(false)
                .help("Check the device for bad blocks before formatting (only supported by ext{2,3,4}, fat32 and ntfs)"),
            Arg::with_name("filesystem")
                .short("f")
                .long("filesystem")
                .takes_value(true)
                .help("Type of filesystem to create")
                .possible_values(&["btrfs", "exfat", "ext2", "ext3", "ext4", "f2fs", "fat32", "ntfs", "udf", "xfs"])
                .default_value("fat32"),
            Arg::with_name("label")
                .short("l")
                .long("label")
                .takes_value(true)
                .help("Set the label of the filesystem"),
            Arg::with_name("table")
                .short("t")
                .long("table")
                .takes_value(true)
                .help("Type of partition table to create")
                .possible_values(&["gpt", "msdos"])
                .default_value("msdos"),
            Arg::with_name("yes")
                .short("y")
                .long("yes")
                .takes_value(false)
                .help("Confirm prompts automatically")
        ])
        .get_matches();

    let device: PathBuf = PathBuf::from(matches.value_of("device").expect("No device specified"));

    let iso: PathBuf = PathBuf::from(matches.value_of("iso").expect("No device specified"));

    if let Err(err) = iso::create_bootable(
        &device,
        &iso,
        matches
            .value_of("filesystem")
            .expect("No filesystem specified"),
        matches
            .value_of("table")
            .expect("No partition table type specified"),
        matches.value_of("label"),
        matches.is_present("badblocks"),
        matches.is_present("yes"),
    ) {
        exit_with_error(err);
    }
}

fn exit_with_error<T: error::USBMakerError>(error: T) -> ! {
    eprintln!("{} {}", Colour::Red.bold().paint("Error:"), error);
    process::exit(error.error_code());
}
