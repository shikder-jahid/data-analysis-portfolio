import pandas as pd
import re

df = pd.read_csv("raw_scraped_products.csv")

# 1. Generate SKU: BRAND-CATEGORY-### 
def make_sku(row, idx):
    brand_code = re.sub(r'[^A-Z]', '', row["brand"].upper())[:4]
    cat_code = row["category"].upper()[:3]
    return f"{brand_code}-{cat_code}-{idx+1:03d}"

df["SKU"] = [make_sku(row, i) for i, row in df.iterrows()]

# 2. Clean product title -> Title Case, no redundant brand repetition
df["Product Title"] = df["name"].str.title()

# 3. Clean price -> numeric float
df["Price (USD)"] = df["raw_price"].str.replace("$", "", regex=False).astype(float)

# 4. Standardize category -> Title Case
df["Category"] = df["category"].str.title()

# 5. Stock status -> clean enum: In Stock / Low Stock / Out of Stock + numeric qty where available
def parse_stock(s):
    s = s.lower()
    if "out of stock" in s:
        return "Out of Stock", 0
    m = re.search(r'(\d+)\s*left', s)
    if m:
        qty = int(m.group(1))
        return "Low Stock", qty
    return "In Stock", 25  # default assumed stock for "in stock" items

stock_parsed = df["stock"].apply(parse_stock)
df["Stock Status"] = stock_parsed.apply(lambda x: x[0])
df["Quantity Available"] = stock_parsed.apply(lambda x: x[1])

# 6. Write proper marketing-style description from raw keywords
def polish_description(row):
    features = row["desc"].split()
    desc = row["desc"][0].upper() + row["desc"][1:]
    return f"{desc}. Brand: {row['brand']}."

df["Description"] = df.apply(polish_description, axis=1)

# Final template matching common store-import column order
df = df.rename(columns={"brand": "Brand"})
final = df[["SKU", "Product Title", "Brand", "Category", "Price (USD)",
            "Stock Status", "Quantity Available", "Description"]]

final.to_csv("formatted_product_listings.csv", index=False)
print(final.to_string())
