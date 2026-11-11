use std::{env, fs, process};

use tally::{parse, report};

fn main() {
    let path = env::args().nth(1).unwrap_or_else(|| {
        eprintln!("usage: tally LEDGER");
        process::exit(2);
    });
    let text = fs::read_to_string(&path).unwrap_or_else(|error| {
        eprintln!("tally: {path}: {error}");
        process::exit(1);
    });
    let ledger = match parse::ledger(&text) {
        Ok(ledger) => ledger,
        Err(error) => {
            eprintln!("tally: {path}:{error}");
            process::exit(1);
        }
    };
    print!("{}", report::render(&ledger));
    println!("total {}", report::money(ledger.total_cents()));
}
