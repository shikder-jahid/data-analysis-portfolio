import pandas as pd
import re

df = pd.read_csv("raw_messy_orders.csv")
original_count = len(df)

# 1. Standardize name casing (Title Case) and strip extra whitespace
df["Customer Name"] = df["Customer Name"].str.strip().str.title().str.replace(r'\s+', ' ', regex=True)

# 2. Clean emails - lowercase, strip whitespace, flag missing
df["Email"] = df["Email"].str.strip().str.lower()
df["Email"] = df["Email"].replace("", pd.NA)

# 3. Standardize phone numbers to a single format: +880XXXXXXXXXX
def clean_phone(phone):
    if pd.isna(phone) or str(phone).strip() == "":
        return pd.NA
    digits = re.sub(r'\D', '', str(phone))
    if digits.startswith('880'):
        digits = digits[3:]
    if digits.startswith('0'):
        digits = digits[1:]
    return f"+880{digits}" if digits else pd.NA

df["Phone"] = df["Phone"].apply(clean_phone)

# 4. Parse all date formats into a single standard: YYYY-MM-DD
def parse_date(date_str):
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%m-%d-%Y", "%d %b %Y"):
        try:
            return pd.to_datetime(date_str, format=fmt).strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue
    return pd.NA

df["Order Date"] = df["Order Date"].apply(parse_date)

# 5. Clean amount - extract numeric value only, standardize as float with 2 decimals
def clean_amount(val):
    if pd.isna(val) or str(val).strip().upper() == "N/A":
        return pd.NA
    num = re.sub(r'[^\d.]', '', str(val))
    try:
        return round(float(num), 2)
    except ValueError:
        return pd.NA

df["Amount (USD)"] = df["Amount"].apply(clean_amount)
df = df.drop(columns=["Amount"])

# 6. Standardize status to Title Case, strip whitespace
df["Order Status"] = df["Order Status"].str.strip().str.title()

# 7. Remove exact duplicate rows
before_dedup = len(df)
df = df.drop_duplicates()
duplicates_removed = before_dedup - len(df)

# 8. Reorder columns cleanly
df = df[["Customer Name", "Email", "Phone", "Order Date", "Amount (USD)", "Order Status"]]

# Report missing data
missing_report = df.isna().sum()

df.to_csv("cleaned_orders.csv", index=False, quoting=1)  # quote all fields so phone/leading-+ numbers stay text

print("=== CLEANED DATA SAMPLE ===")
print(df.head(10).to_string())
print(f"\nOriginal rows: {original_count}")
print(f"Duplicates removed: {duplicates_removed}")
print(f"Final rows: {len(df)}")
print(f"\nMissing values by column:\n{missing_report}")
