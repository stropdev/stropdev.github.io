# tally

Reads a ledger, one entry per line, and prints totals per account.

    2026-03-02  groceries   -42.10
    2026-03-03  salary     3100.00

Amounts are kept as whole cents; `total_cents` never goes through a float.
