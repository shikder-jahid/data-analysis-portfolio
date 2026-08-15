import pandas as pd
import random
from mlxtend.frequent_patterns import apriori, association_rules
from mlxtend.preprocessing import TransactionEncoder

random.seed(42)

# Simulate realistic e-commerce transaction data (like a retail store's order history)
products = {
    "electronics": ["Wireless Mouse", "USB-C Cable", "Laptop Stand", "Bluetooth Speaker", "Phone Case", "Screen Protector", "Power Bank"],
    "kitchen": ["Coffee Mug", "French Press", "Kitchen Scale", "Cutting Board", "Water Bottle"],
    "office": ["Notebook", "Desk Organizer", "Sticky Notes", "Pen Set", "Desk Lamp"],
}

# common combos to simulate real buying patterns (so rules actually emerge)
combo_rules = [
    (["Wireless Mouse", "Laptop Stand"], 0.35),
    (["USB-C Cable", "Power Bank"], 0.30),
    (["Coffee Mug", "French Press"], 0.25),
    (["Notebook", "Pen Set"], 0.30),
    (["Desk Organizer", "Desk Lamp", "Notebook"], 0.20),
    (["Phone Case", "Screen Protector"], 0.40),
]

all_products = [p for cat in products.values() for p in cat]

transactions = []
for _ in range(500):
    basket = set()
    # chance of following a known combo
    for combo, prob in combo_rules:
        if random.random() < prob:
            basket.update(combo)
    # add 1-3 random extra items
    for _ in range(random.randint(1, 3)):
        basket.add(random.choice(all_products))
    if len(basket) >= 2:
        transactions.append(list(basket))

# Save raw transactions (looks like exported order data)
raw_df = pd.DataFrame({"transaction_id": range(1, len(transactions)+1),
                        "items": [", ".join(t) for t in transactions]})
raw_df.to_csv("raw_transactions.csv", index=False)

# Encode transactions for mining
te = TransactionEncoder()
te_ary = te.fit(transactions).transform(transactions)
df = pd.DataFrame(te_ary, columns=te.columns_)

# Frequent itemsets
frequent_itemsets = apriori(df, min_support=0.05, use_colnames=True)
frequent_itemsets = frequent_itemsets.sort_values("support", ascending=False)

# Association rules
rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)
rules = rules.sort_values("lift", ascending=False)
rules_out = rules[["antecedents", "consequents", "support", "confidence", "lift"]].copy()
rules_out["antecedents"] = rules_out["antecedents"].apply(lambda x: ", ".join(list(x)))
rules_out["consequents"] = rules_out["consequents"].apply(lambda x: ", ".join(list(x)))
rules_out = rules_out.round(3)

frequent_itemsets_out = frequent_itemsets.copy()
frequent_itemsets_out["itemsets"] = frequent_itemsets_out["itemsets"].apply(lambda x: ", ".join(list(x)))
frequent_itemsets_out = frequent_itemsets_out.round(3)

frequent_itemsets_out.to_csv("frequent_itemsets.csv", index=False)
rules_out.to_csv("association_rules.csv", index=False)

print("=== TOP ASSOCIATION RULES ===")
print(rules_out.head(10).to_string(index=False))
print(f"\nTotal transactions: {len(transactions)}")
print(f"Frequent itemsets found: {len(frequent_itemsets)}")
print(f"Association rules found: {len(rules)}")
