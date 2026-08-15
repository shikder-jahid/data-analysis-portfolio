# Data Formatting & Cleaning — E-commerce Order Export

## Objective
Take a raw, inconsistently formatted order export (the kind that comes straight from a store's backend or a client's spreadsheet) and standardize it into a clean, analysis-ready dataset.

## Problems Found in Raw Data
- Inconsistent name capitalization (`chen wei`, `MARY JONES`) and extra whitespace
- Emails with mixed case and stray spaces
- Phone numbers in 3+ different formats (with/without country code, parentheses, dashes)
- Dates in 4 different formats (`DD/MM/YYYY`, `YYYY-MM-DD`, `MM-DD-YYYY`, `DD Mon YYYY`)
- Currency values written inconsistently (`$317.16`, `186.0 USD`, `USD 43.42`, plain numbers)
- Inconsistent status casing (`Delivered`, `delivered`, `DELIVERED`)
- Duplicate rows and missing values

## What Was Done
1. Standardized names to Title Case, trimmed whitespace
2. Normalized emails to lowercase
3. Reformatted all phone numbers to a single international format (`+880XXXXXXXXXX`)
4. Parsed all date formats into ISO standard (`YYYY-MM-DD`)
5. Extracted numeric values from currency strings into a clean `Amount (USD)` column
6. Standardized status values to consistent Title Case
7. Removed exact duplicate rows
8. Flagged missing values instead of silently dropping them

## Tools
Python, pandas, regex

## Files
- `raw_messy_orders.csv` — original unclean export (input)
- `cleaned_orders.csv` — final standardized dataset (output)
- `before_after_comparison.png` — visual side-by-side comparison
- `clean_data.py` — the cleaning script
