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

use std::fs::File;
use std::io::{self, Read, Write};
use std::path::Path;
use std::sync::mpsc;
use std::thread;
use std::time;

use indicatif::{ProgressBar, ProgressDrawTarget, ProgressStyle};

use error::DdError;
use tui;

pub fn dd(input: &Path, output: &Path, assume_yes: bool, disable_ui: bool) -> Result<(), DdError> {
    let mut input_file: File = match File::open(&input) {
        Ok(file) => file,
        Err(err) => return Err(DdError::InputFileOpenError(err)),
    };

    let file_size: u64 = match input_file.metadata() {
        Ok(metadata) => metadata.len(),
        Err(err) => return Err(DdError::InputFileMetadataError(err)),
    };

    if !assume_yes && output.is_file() {
        match tui::prompt(&*format!("Do you want to overwrite {:?}?", output), false) {
            true => (),
            false => return Err(DdError::CanceledByUser),
        }
    }

    let mut output_file: File = match File::create(&output) {
        Ok(file) => file,
        Err(err) => return Err(DdError::OutputFileOpenError(err)),
    };

    // Allocate a buffer used to copy data.
    // 131072B == 128 KiB
    // https://eklitzke.org/efficient-file-copying-on-linux
    // http://git.savannah.gnu.org/cgit/coreutils.git/tree/src/ioblksize.h
    let mut buf: [u8; 131072] = [0; 131072];

    // The progress bar/machine readable output is done in a separate thread.
    let (tx, rx) = mpsc::channel();

    let ui_handle = thread::spawn(move || {
        let mut written: u64 = 0;

        // If the machine readable flag is set, print the size of data to copy,
        // then print how many bytes have been copied (separated by newlines).
        // Else draw a fancy progress bar.
        if disable_ui {
            println!("{}", file_size);
            loop {
                println!("{}", written);
                written += match rx.recv() {
                    Ok(len) => len as u64,
                    Err(_) => break,
                }
            }
        } else {
            let progress_bar = ProgressBar::new(file_size);
            progress_bar.set_draw_target(ProgressDrawTarget::stdout());
            progress_bar.set_style(
                ProgressStyle::default_bar()
                    .template("{spinner} {percent:3}%▕{wide_bar}▏{bytes}/{total_bytes}")
                    .progress_chars("█▉▊▋▌▍▎▏  "),
            );

            loop {
                written += match rx.recv() {
                    Ok(len) => len as u64,
                    Err(_) => {
                        progress_bar.finish();
                        break;
                    }
                };
                progress_bar.set_position(written);
            }
        }
    });

    let start: time::Instant = time::Instant::now();

    // Perform the copy operation.
    // Based on std::io::copy (https://doc.rust-lang.org/nightly/std/io/fn.copy.html).
    loop {
        let len: usize = match input_file.read(&mut buf) {
            Ok(0) => break,
            Ok(len) => len,
            Err(ref err) if err.kind() == io::ErrorKind::Interrupted => continue,
            Err(err) => return Err(DdError::ReadError(err)),
        };
        match output_file.write_all(&buf[..len]) {
            Ok(_) => (),
            Err(err) => return Err(DdError::WriteError(err)),
        };
        tx.send(len).ok();
    }

    // This makes rx.recv() in the second thread return Err,
    // which makes it cleanup and exit
    drop(tx);
    ui_handle.join().ok();

    let spinner = ProgressBar::hidden();

    if !disable_ui {
        spinner.set_draw_target(ProgressDrawTarget::stdout());
        spinner.set_style(ProgressStyle::default_spinner());
        spinner.set_message("Finishing...");
        spinner.enable_steady_tick(100);
    }

    match output_file.sync_all() {
        Ok(_) => (),
        Err(err) => return Err(DdError::SyncError(err)),
    }

    spinner.finish();

    if !disable_ui {
        println!("Took {} seconds to complete.", start.elapsed().as_secs());
    }

    Ok(())
}
