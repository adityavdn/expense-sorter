# Expense Sorter

A practical expense categorisation tool that learns from your corrections and sorts bank transactions automatically.

## Overview

Expense Sorter reads bank statement data, identifies likely merchant categories and asks only when confidence is low. As you correct the predictions, the tool learns from those corrections and improves future classification.

## How it works

- recognises common UK merchants and categories
- applies a rule-based and probabilistic approach to classify transactions
- remembers prior corrections to reduce repeated prompts
- supports CSV exports from major banks and fintech providers

## Tech Stack

- Python
- CSV processing
- Naive Bayes-style classification

## How to run

```bash
python3 sorter.py statement.csv
```

Optional commands:

```bash
python3 sorter.py statement.csv --no-ask
python3 sorter.py learn statement_sorted.csv
```

## Project structure

```text
.
├── sorter.py
├── test_sorter.py
├── sample_statement.csv
├── README.md
└── supporting data files
```

