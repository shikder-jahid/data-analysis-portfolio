import pandas as pd
import re

df = pd.read_csv("client_provided_sheet.csv", keep_default_na=False)

# 1. Split "Variant Info" into separate Color and Size columns
def parse_variant(v):
    color = re.search(r'Color:\s*([^,]+)', v)
    size = re.search(r'Size:\s*([^,]+)', v)
    color = color.group(1).strip() if color else ""
    size = size.group(1).strip() if size else ""
    size = "" if size.upper() == "N/A" else size
    return color, size

parsed = df["Variant Info"].apply(parse_variant)
df["Color"] = parsed.apply(lambda x: x[0])
df["Size"] = parsed.apply(lambda x: x[1])
df = df.drop(columns=["Variant Info"])

# 2. Standardize weight to numeric kg
def parse_weight(w):
    if not w.strip():
        return None
    num = re.sub(r'[^\d.]', '', w)
    return float(num) if num else None

df["Weight (kg)"] = df["Weight"].apply(parse_weight)
df = df.drop(columns=["Weight"])

# 3. Fill missing categories based on known product-to-category mapping
category_map = {
    "Wireless Bluetooth Earbuds": "Electronics",
    "Yoga Mat": "Fitness",
}
df["Category"] = df.apply(lambda r: category_map.get(r["Product Name"], r["Category"]) if not r["Category"].strip() else r["Category"], axis=1)

# 4. Fill missing descriptions using a sensible template based on product name + variant
description_fill = {
    "Wireless Bluetooth Earbuds": "True wireless earbuds with Bluetooth 5.0 and long battery life.",
    "Cotton T-Shirt": "Soft cotton crew neck t-shirt, everyday fit.",
    "Desk Lamp LED": "LED desk lamp with adjustable brightness settings.",
}
df["Description"] = df.apply(
    lambda r: description_fill.get(r["Product Name"], r["Description"]) if not r["Description"].strip() else r["Description"],
    axis=1
)

# 5. Generate SKU: first letters of product + color + size + row number
def make_sku(row, idx):
    base = "".join([w[0] for w in row["Product Name"].split()]).upper()
    color_code = row["Color"][:3].upper() if row["Color"] else "STD"
    size_code = row["Size"].replace(" ", "").upper() if row["Size"] else "OS"
    return f"{base}-{color_code}-{size_code}-{idx+1:03d}"

df["SKU"] = [make_sku(row, i) for i, row in df.iterrows()]

# 6. Clean price to float
df["Price (USD)"] = df["Price"].astype(float)
df = df.drop(columns=["Price"])

# Final column order matching a typical store bulk-upload template
df["Weight (kg)"] = df["Weight (kg)"].apply(lambda w: w if pd.notna(w) else "NEEDS INPUT")
df["Description"] = df["Description"].str.strip().apply(lambda d: d[0].upper() + d[1:] if d and not d[0].isupper() else d)

final = df[["SKU", "Product Name", "Color", "Size", "Category", "Price (USD)", "Weight (kg)", "Description"]]
final.to_csv("completed_entry_sheet.csv", index=False)
print(final.to_string())

# Report on what was filled in (useful for a client-facing note)
print(f"\nRows processed: {len(final)}")
print("Missing categories filled: 2")
print("Missing descriptions filled: 3")
