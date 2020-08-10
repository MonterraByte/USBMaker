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

mod copy;
mod error;
mod formatting;
mod iso;
mod mount;
mod partitioning;

use std::io::{self, Write};
use std::path::PathBuf;
use std::process;

use ansi_term::Colour;
use clap::Clap;

use crate::formatting::FileSystem;

#[derive(Clap, Debug)]
#[clap(about, author, version)]
struct Args {
    /// Path to the ISO file
    iso: PathBuf,
    /// Path to the device file
    device: PathBuf,
    /// Check for bad blocks while formatting
    #[clap(short, long)]
    badblocks: bool,
    /// Filesystem used to format the device
    #[clap(short, long, possible_values = &["btrfs", "exfat", "ext2", "ext3", "ext4", "f2fs", "fat32", "ntfs", "udf", "xfs"], default_value = "fat32")]
    filesystem: FileSystem,
    /// Partition table used on the device
    #[clap(short, long, possible_values = &["gpt", "msdos"], default_value = "msdos")]
    table: String,
    /// Label to give to the filesystem (to use the default, don't pass this option)
    #[clap(short, long)]
    label: Option<String>,
    /// Do not prompt for confirmation
    #[clap(short = "y", long = "yes")]
    force_yes: bool,
}

fn main() {
    let args = Args::parse();

    if !args.force_yes {
        eprintln!("{}", Colour::Red.underline().paint(format!("This will wipe all data on {}.", args.device.display())));

        let mut input: String = String::with_capacity(2);
        loop {
            eprint!("Do you want to continue? [Y/n] ");
            let _ = io::stderr().flush();
            if let Err(err) = io::stdin().read_line(&mut input) {
                eprintln!("Error reading input: {}", err);
                input.clear();
                continue;
            }

            match input.to_lowercase().trim() {
                "" | "y" | "yes" => break,
                "n" | "no" => return,
                _ => input.clear(),
            }
        }
    }

    if let Err(err) = iso::create_bootable(
        &args.device,
        &args.iso,
        args.filesystem,
        &args.table,
        args.label.as_deref(),
        args.badblocks,
    ) {
        eprintln!("{} {}", Colour::Red.bold().paint("Error:"), err);
        process::exit(err.error_code());
    }
}
