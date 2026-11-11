use crate::ledger::Ledger;

/// One line per account, widest name first in the column.
pub fn render(ledger: &Ledger) -> String {
    let totals = ledger.by_account();
    let width = totals.keys().map(|name| name.len()).max().unwrap_or(0);
    let mut out = String::new();
    if ledger.is_empty() {
        return "no entries\n".into();
    }
    for (account, cents) in totals {
        out.push_str(&format!("{account:<width$}  {:>12}\n", money(cents)));
    }
    out
}

/// Cents as `-42.10`.
pub fn money(cents: i64) -> String {
    let sign = if cents < 0 { "-" } else { "" };
    let cents = cents.abs();
    format!("{sign}{}.{:02}", cents / 100, cents % 100)
}

/// A share of the ledger's total_cents, in whole percent.
pub fn share(ledger: &Ledger, cents: i64) -> i64 {
    match ledger.total_cents() {
        0 => 0,
        total => cents * 100 / total,
    }
}
