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
use std::io::{self, Write};

use ansi_term::{Colour, Style};

pub fn prompt(message: &str, default: bool) -> bool {
    let message_style: Style = Colour::White.bold();
    let prompt_style: Style = Colour::Blue.normal();
    let mut input: String = String::with_capacity(2);
    loop {
        match default {
            true => eprint!(
                "{} {} ",
                message_style.paint(message),
                prompt_style.paint("[Y/n]")
            ),
            false => eprint!(
                "{} {} ",
                message_style.paint(message),
                prompt_style.paint("[y/N]")
            ),
        }
        if let Err(err) = io::stdout().flush() {
            eprintln!("Error writing to stdout: {}", err.description());
        }

        if let Err(err) = io::stdin().read_line(&mut input) {
            eprintln!("Error reading input: {}", err.description());
            input.clear();
            continue;
        }

        match input.to_lowercase().trim() {
            "" => return default,
            "y" | "yes" => return true,
            "n" | "no" => return false,
            _ => (),
        }

        input.clear()
    }
}

pub fn warn(warning: &str) {
    let warning_style: Style = Colour::Red.underline();
    eprintln!("{}", warning_style.paint(warning));
}
