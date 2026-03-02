import pandas as pd
from pathlib import Path

DATA_PATH = Path("data/transactions_3months.csv")
BUDGET_PATH = Path("data/budgets.csv")
OUT_DIR = Path("outputs")
OUT_DIR.mkdir(exist_ok=True)

df = pd.read_csv(DATA_PATH)
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
df["type"] = df["type"].astype(str).str.strip().str.lower()
df["category"] = df["category"].astype(str).str.strip()

df["month"] = df["date"].dt.to_period("M")
df["category_group"] = df["category"].replace({"Food_home": "Food", "Food_out": "Food"})

# Actual monthly expense by category
actual = (
    df[df["type"] == "expense"]
    .groupby(["month", "category_group"])["amount"]
    .sum()
    .reset_index()
)

budgets = pd.read_csv(BUDGET_PATH)
budgets["category_group"] = budgets["category_group"].astype(str).str.strip()
budgets["budget_monthly"] = pd.to_numeric(budgets["budget_monthly"], errors="coerce")

# Join budget
merged = actual.merge(budgets, on="category_group", how="left")

# Variance
merged["variance"] = merged["amount"] - merged["budget_monthly"]
merged["variance_pct"] = merged.apply(
    lambda r: (r["variance"] / r["budget_monthly"]) if r["budget_monthly"] else None,
    axis=1
)

# Sort: biggest over-budget first
report = merged.sort_values(["month", "variance"], ascending=[True, False])

report.to_csv(OUT_DIR / "budget_vs_actual.csv", index=False)

print("✅ Saved outputs/budget_vs_actual.csv")
print("\nTop over-budget rows:")
print(report[report["variance"] > 0].head(15))