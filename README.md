# Expense Sorter

Categorises your bank statement and **learns from every correction you make**. It's pure
Python and runs offline, so your data never leaves your laptop.

```bash
python3 sorter.py statement.csv
```

```
  PUREGYM LTD   £24.99
  1.Bills   2.Cash   3.Eating out   4.Groceries   5.Shopping ...
  Category? [type a number or new category]: Fitness

Spending by category  (20 transactions, asked you about 2)
  Bills           £   723.00  ██████████████████████
  Fitness         £    49.98  ██
  Groceries       £    52.15  ██
  ...
```

**How it learns**
- It knows common UK merchants (Tesco, TfL, Netflix and so on) from the start.
- It only asks about transactions it isn't sure of. Your answer is remembered, so that
  merchant is never asked about again.
- Words generalise: once you've labelled `PUREGYM` as Fitness, it will guess `THE GYM GROUP` as Fitness too.
  Under the hood this is naive Bayes plus an exact-merchant memory, stored in `brain.json`.

**Other commands**
- `python3 sorter.py statement.csv --no-ask` sorts without asking any questions.
- `python3 sorter.py learn statement_sorted.csv` learns from a sorted file you fixed by hand in Excel or Numbers.

It works with CSV exports from Monzo, Barclays, Lloyds, Revolut and others: it spots the
description column and either a single amount column or separate paid-in/paid-out columns.
Try it with `sample_statement.csv`. Run the tests with `python3 test_sorter.py`.
