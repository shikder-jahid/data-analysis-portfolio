#!/usr/bin/env python3
"""
Data Cleaning Pipeline
-----------------------
A general-purpose automation tool that cleans messy CSV/Excel files:
- Standardizes column names
- Strips whitespace from text
- Removes duplicate rows
- Handles missing values (drop mostly-empty columns, fill the rest)
- Auto-detects and fixes numeric/date columns stored as text
- Outputs a cleaned file + a human-readable change report

Usage:
    python clean_pipeline.py input.csv
    python clean_pipeline.py input.xlsx --output-dir results --missing-threshold 0.6
"""

import warnings
import pandas as pd
import numpy as np
import argparse
import os
from datetime import datetime

warnings.filterwarnings("ignore")


class DataCleaner:
    def __init__(self, filepath, missing_threshold=0.5, output_dir="cleaned_output"):
        self.filepath = filepath
        self.missing_threshold = missing_threshold
        self.output_dir = output_dir
        self.df = None
        self.original_shape = None
        self.log = []

    def _log(self, msg):
        self.log.append(msg)
        print(msg)

    def load(self):
        ext = os.path.splitext(self.filepath)[1].lower()
        if ext == ".csv":
            self.df = pd.read_csv(self.filepath)
        elif ext in (".xlsx", ".xls"):
            self.df = pd.read_excel(self.filepath)
        else:
            raise ValueError(f"Unsupported file type: {ext}")
        self.original_shape = self.df.shape
        self._log(f"Loaded '{self.filepath}' — shape {self.original_shape}")
        return self

    def clean_column_names(self):
        original_cols = list(self.df.columns)
        self.df.columns = (
            self.df.columns.astype(str)
            .str.strip()
            .str.lower()
            .str.replace(r"[^\w\s]", "", regex=True)
            .str.replace(r"\s+", "_", regex=True)
        )
        changed = sum(a != b for a, b in zip(original_cols, self.df.columns))
        self._log(f"Standardized {changed} column name(s)")
        return self

    def strip_whitespace(self):
        str_cols = self.df.select_dtypes(include="object").columns
        for col in str_cols:
            self.df[col] = self.df[col].astype(str).str.strip()
            self.df[col] = self.df[col].replace({"nan": np.nan, "None": np.nan, "": np.nan})
        self._log(f"Trimmed whitespace on {len(str_cols)} text column(s)")
        return self

    def drop_empty_rows(self):
        before = len(self.df)
        self.df = self.df.dropna(how="all")
        removed = before - len(self.df)
        self._log(f"Dropped {removed} fully empty row(s)")
        return self

    def remove_duplicates(self):
        before = len(self.df)
        self.df = self.df.drop_duplicates()
        removed = before - len(self.df)
        self._log(f"Removed {removed} duplicate row(s)")
        return self

    def handle_missing(self):
        missing_pct = self.df.isnull().mean()
        cols_to_drop = missing_pct[missing_pct > self.missing_threshold].index.tolist()
        if cols_to_drop:
            self.df = self.df.drop(columns=cols_to_drop)
            self._log(
                f"Dropped {len(cols_to_drop)} column(s) with >{self.missing_threshold * 100:.0f}% missing: {cols_to_drop}"
            )

        for col in self.df.columns:
            missing_count = self.df[col].isnull().sum()
            if missing_count == 0:
                continue
            if pd.api.types.is_datetime64_any_dtype(self.df[col]):
                self._log(f"Left {missing_count} missing date(s) in '{col}' as blank (no safe placeholder)")
            elif pd.api.types.is_numeric_dtype(self.df[col]):
                fill_val = self.df[col].median()
                self.df[col] = self.df[col].fillna(fill_val)
                self._log(f"Filled {missing_count} missing value(s) in '{col}' with median ({fill_val})")
            else:
                self.df[col] = self.df[col].fillna("Unknown")
                self._log(f"Filled {missing_count} missing value(s) in '{col}' with 'Unknown'")
        return self

    def fix_dtypes(self):
        for col in self.df.select_dtypes(include="object").columns:
            non_null = self.df[col].dropna()
            if len(non_null) == 0:
                continue

            numeric_converted = pd.to_numeric(non_null, errors="coerce")
            if numeric_converted.notnull().sum() / len(non_null) > 0.9:
                self.df[col] = pd.to_numeric(self.df[col], errors="coerce")
                self._log(f"Converted '{col}' to numeric")
                continue

            date_converted = pd.to_datetime(non_null, errors="coerce", format="mixed")
            if date_converted.notnull().sum() / len(non_null) > 0.9:
                self.df[col] = pd.to_datetime(self.df[col], errors="coerce", format="mixed")
                self._log(f"Converted '{col}' to datetime")
        return self

    def save(self):
        os.makedirs(self.output_dir, exist_ok=True)
        base = os.path.splitext(os.path.basename(self.filepath))[0]

        out_path = os.path.join(self.output_dir, f"{base}_cleaned.csv")
        self.df.to_csv(out_path, index=False)
        self._log(f"Saved cleaned file to '{out_path}'")

        report_path = os.path.join(self.output_dir, f"{base}_report.txt")
        with open(report_path, "w") as f:
            f.write("DATA CLEANING REPORT\n")
            f.write("=" * 50 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source file: {self.filepath}\n")
            f.write(f"Original shape: {self.original_shape[0]} rows x {self.original_shape[1]} columns\n")
            f.write(f"Final shape:    {self.df.shape[0]} rows x {self.df.shape[1]} columns\n\n")
            f.write("STEPS PERFORMED:\n")
            f.write("-" * 50 + "\n")
            for line in self.log:
                f.write(f"- {line}\n")
        self._log(f"Saved report to '{report_path}'")

        return out_path, report_path

    def run(self):
        (
            self.load()
            .clean_column_names()
            .strip_whitespace()
            .drop_empty_rows()
            .remove_duplicates()
            .fix_dtypes()
            .handle_missing()
        )
        return self.save()


def main():
    parser = argparse.ArgumentParser(description="Automatically clean a CSV or Excel file")
    parser.add_argument("input", help="Path to input CSV/Excel file")
    parser.add_argument("--output-dir", default="cleaned_output", help="Directory to save cleaned file + report")
    parser.add_argument(
        "--missing-threshold",
        type=float,
        default=0.5,
        help="Drop columns with more than this fraction missing (default: 0.5)",
    )
    args = parser.parse_args()

    cleaner = DataCleaner(args.input, missing_threshold=args.missing_threshold, output_dir=args.output_dir)
    cleaner.run()


if __name__ == "__main__":
    main()
