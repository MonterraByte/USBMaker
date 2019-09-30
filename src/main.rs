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
use structopt::StructOpt;

use error::USBMakerError;

#[derive(StructOpt, Debug)]
#[structopt(about, author)]
struct Args {
    /// Path to the ISO file
    iso: PathBuf,
    /// Path to the device file
    device: PathBuf,
    /// Check for bad blocks while formatting
    #[structopt(short, long)]
    badblocks: bool,
    /// Filesystem used to format the device
    #[structopt(short, long, possible_values = &["btrfs", "exfat", "ext2", "ext3", "ext4", "f2fs", "fat32", "ntfs", "udf", "xfs"], default_value = "fat32")]
    filesystem: String,
    /// Partition table used on the device
    #[structopt(short, long, possible_values = &["gpt", "msdos"], default_value = "msdos")]
    table: String,
    /// Label to give to the filesystem (to use the default, don't pass this option)
    #[structopt(short, long)]
    label: Option<String>,
    /// Do not prompt for confirmation
    #[structopt(short = "y", long = "yes")]
    force_yes: bool,
}

#[paw::main]
fn main(args: Args) {
    if let Err(err) = iso::create_bootable(
        &args.device,
        &args.iso,
        &args.filesystem,
        &args.table,
        args.label.as_ref().map(|s| s.as_str()),
        args.badblocks,
        args.force_yes,
    ) {
        eprintln!("{} {}", Colour::Red.bold().paint("Error:"), err);
        process::exit(err.error_code());
    }
}
