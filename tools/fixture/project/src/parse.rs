use crate::ledger::{Entry, Ledger};

/// Parse a ledger: `DATE ACCOUNT AMOUNT` per line, `#` starts a comment.
/// The error names the line it came from.
pub fn ledger(text: &str) -> Result<Ledger, String> {
    let mut ledger = Ledger::default();
    for (index, line) in text.lines().enumerate() {
        let line = line.split('#').next().unwrap_or("").trim();
        if line.is_empty() {
            continue;
        }
        let mut fields = line.split_whitespace();
        let (Some(date), Some(account), Some(amount), None) =
            (fields.next(), fields.next(), fields.next(), fields.next())
        else {
            return Err(format!("{}: expected DATE ACCOUNT AMOUNT", index + 1));
        };
        let cents = cents(amount).ok_or_else(|| format!("{}: bad amount {amount}", index + 1))?;
        ledger.push(Entry { date: date.into(), account: account.into(), cents });
    }
    Ok(ledger)
}

/// `-42.10` is -4210. At most two decimals; no float on the way.
fn cents(amount: &str) -> Option<i64> {
    let (sign, digits) = match amount.strip_prefix('-') {
        Some(rest) => (-1, rest),
        None => (1, amount),
    };
    let (whole, fraction) = digits.split_once('.').unwrap_or((digits, "0"));
    if fraction.len() > 2 || fraction.is_empty() {
        return None;
    }
    let whole: i64 = whole.parse().ok()?;
    let fraction: i64 = format!("{fraction:0<2}").parse().ok()?;
    Some(sign * (whole * 100 + fraction))
}
