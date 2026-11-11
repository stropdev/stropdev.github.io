use tally::{ledger::Entry, ledger::Ledger, report};

fn sample() -> Ledger {
    let mut ledger = Ledger::default();
    for (account, cents) in [("groceries", -4210), ("salary", 310000), ("groceries", -1890)] {
        ledger.push(Entry { date: "2026-03-02".into(), account: account.into(), cents });
    }
    ledger
}

#[test]
fn total_cents_sums_every_entry() {
    assert_eq!(sample().total_cents(), 303900);
}

#[test]
fn report_has_one_line_per_account() {
    let text = report::render(&sample());
    assert_eq!(text.lines().count(), 2);
    assert!(text.contains("groceries"));
}
