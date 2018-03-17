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

extern crate ansi_term;
#[macro_use]
extern crate clap;
extern crate indicatif;

mod dd;
mod error;
mod tui;

use std::path::PathBuf;
use std::process;

use ansi_term::Colour;
use clap::{App, Arg, SubCommand};

fn main() {
    let matches = App::new("USBMaker")
        .author(crate_authors!())
        .version(crate_version!())
        .about("Create bootable usb drives")
        .subcommand(
            SubCommand::with_name("dd")
                .author(crate_authors!())
                .version(crate_version!())
                .about("Copies the contents of a file/device to another file/device")
                .args(&[
                    Arg::with_name("input")
                        .takes_value(true)
                        .required(true)
                        .index(1)
                        .help("Device or file from which data is copied"),
                    Arg::with_name("output")
                        .takes_value(true)
                        .required(true)
                        .index(2)
                        .help("Device or file to which data is copied"),
                    Arg::with_name("yes")
                        .short("y")
                        .long("yes")
                        .takes_value(false)
                        .help("Confirm prompts automatically"),
                    Arg::with_name("machine-readable")
                        .short("M")
                        .long("machine-readable")
                        .takes_value(false)
                        .help("Prints output that can be interpreted by other programs (for non-interactive use)")
                ]),
        )
        .get_matches();

    match matches.subcommand() {
        ("dd", Some(sub_matches)) => {
            let input: PathBuf = PathBuf::from(
                sub_matches
                    .value_of("input")
                    .expect("No input file specified"),
            );
            let output: PathBuf = PathBuf::from(
                sub_matches
                    .value_of("output")
                    .expect("No output file specified"),
            );

            match dd::dd(
                &input,
                &output,
                sub_matches.is_present("yes"),
                sub_matches.is_present("machine-readable"),
            ) {
                Ok(_) => (),
                Err(err) => exit_with_error(err),
            }
        }
        _ => (),
    }
}

fn exit_with_error<T: error::USBMakerError>(error: T) -> ! {
    eprintln!("{} {}", Colour::Red.bold().paint("Error:"), error);
    process::exit(error.error_code());
}
