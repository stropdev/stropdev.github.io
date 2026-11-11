use std::collections::BTreeMap;

/// One dated line of the ledger. Amounts are whole cents.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Entry {
    pub date: String,
    pub account: String,
    pub cents: i64,
}

#[derive(Debug, Default)]
pub struct Ledger {
    entries: Vec<Entry>,
}

impl Ledger {
    pub fn push(&mut self, entry: Entry) {
        self.entries.push(entry);
    }

    pub fn entries(&self) -> &[Entry] {
        &self.entries
    }

    /// The sum of every entry.
    pub fn total_cents(&self) -> i64 {
        self.entries.iter().map(|entry| entry.cents).sum()
    }

    /// The sum per account, in account order.
    pub fn by_account(&self) -> BTreeMap<&str, i64> {
        let mut totals = BTreeMap::new();
        for entry in &self.entries {
            *totals.entry(entry.account.as_str()).or_insert(0) += entry.cents;
        }
        totals
    }
}
