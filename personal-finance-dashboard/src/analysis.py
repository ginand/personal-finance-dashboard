import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

DATA_PATH = Path("data/transactions_3months.csv")
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

# =========================
# 1) Load + Validate
# =========================
df = pd.read_csv(DATA_PATH)

# Parse types
df["date"] = pd.to_datetime(df["date"], errors="coerce")
df["amount"] = pd.to_numeric(df["amount"], errors="coerce")

# Clean text
for col in ["type", "category", "merchant", "payment_method", "description"]:
    if col in df.columns:
        df[col] = df[col].astype(str).str.strip()

df["type"] = df["type"].str.lower()

# Basic data quality checks
bad_date = df[df["date"].isna()]
bad_amount = df[df["amount"].isna()]
if len(bad_date) > 0:
    print("❌ Bad date rows:")
    print(bad_date.head(10))
    raise SystemExit("Stop: invalid date parsing.")
if len(bad_amount) > 0:
    print("❌ Bad amount rows:")
    print(bad_amount.head(10))
    raise SystemExit("Stop: invalid amount parsing.")

valid_types = {"income", "expense"}
invalid_type = df[~df["type"].isin(valid_types)]
if len(invalid_type) > 0:
    print("❌ Invalid type rows (must be income/expense):")
    print(invalid_type[["date", "description", "type", "amount"]].head(20))
    raise SystemExit("Stop: invalid type values.")

# Amount should be positive in this modeling style
neg_amount = df[df["amount"] < 0]
if len(neg_amount) > 0:
    print("⚠ Found negative amounts. Recommended: keep amount positive + use type to sign.")
    print(neg_amount.head(10))

# De-duplicate (optional heuristic)
# If the same date+merchant+amount+description repeats, treat as duplicate
dup_mask = df.duplicated(subset=["date", "merchant", "amount", "description", "type"], keep="first")
dup_count = int(dup_mask.sum())
if dup_count > 0:
    print(f"⚠ Removing duplicates: {dup_count}")
    df = df[~dup_mask].copy()

# =========================
# 2) Feature engineering
# =========================
df["month"] = df["date"].dt.to_period("M")
df["weekday"] = df["date"].dt.weekday
df["is_weekend"] = df["weekday"] >= 5

# Group categories for better reporting
# Keep rent/utilities/etc intact; merge Food_home/out
df["category_group"] = df["category"].replace({
    "Food_home": "Food",
    "Food_out": "Food"
})

# Fixed vs variable (simple rule)
fixed_categories = {"Rent", "Utilities", "Health"}
df["cost_type"] = df["category_group"].apply(lambda c: "Fixed" if c in fixed_categories else "Variable")

# =========================
# 3) Overall KPI
# =========================
total_income = df.loc[df["type"] == "income", "amount"].sum()
total_expense = df.loc[df["type"] == "expense", "amount"].sum()
saving = total_income - total_expense
saving_rate = (saving / total_income) if total_income != 0 else 0

print("\n===== OVERALL KPI =====")
print(f"Total income : {total_income:,.0f}")
print(f"Total expense: {total_expense:,.0f}")
print(f"Saving       : {saving:,.0f}")
print(f"Saving rate  : {saving_rate*100:.2f}%")

# =========================
# 4) Monthly summary + MoM
# =========================
monthly_income = (
    df[df["type"] == "income"]
    .groupby("month")["amount"]
    .sum()
    .sort_index()
)
monthly_expense = (
    df[df["type"] == "expense"]
    .groupby("month")["amount"]
    .sum()
    .sort_index()
)

monthly_summary = pd.DataFrame({"income": monthly_income, "expense": monthly_expense}).fillna(0)
monthly_summary["saving"] = monthly_summary["income"] - monthly_summary["expense"]
monthly_summary["saving_rate"] = (monthly_summary["saving"] / monthly_summary["income"]).replace([float("inf")], 0).fillna(0)

# MoM change (expense)
monthly_summary["expense_mom_change"] = monthly_summary["expense"].diff()
monthly_summary["expense_mom_pct"] = monthly_summary["expense"].pct_change().replace([float("inf"), float("-inf")], 0).fillna(0)

print("\n===== MONTHLY SUMMARY =====")
print(monthly_summary)

monthly_summary.to_csv(OUTPUT_DIR / "monthly_summary.csv")

# =========================
# 5) Category breakdown
# =========================
category_expense = (
    df[df["type"] == "expense"]
    .groupby("category_group")["amount"]
    .sum()
    .sort_values(ascending=False)
)
print("\n===== EXPENSE BY CATEGORY (GROUPED) =====")
print(category_expense)

expense_total = total_expense if total_expense != 0 else 1
category_share = (category_expense / expense_total * 100).round(2)
print("\nTop category share (%):")
print(category_share.head(10).astype(str) + "%")

category_expense.to_csv(OUTPUT_DIR / "expense_by_category.csv")

# =========================
# 6) Fixed vs Variable
# =========================
fixed_variable = (
    df[df["type"] == "expense"]
    .groupby("cost_type")["amount"]
    .sum()
    .sort_values(ascending=False)
)
print("\n===== FIXED vs VARIABLE =====")
print(fixed_variable)

fixed_variable_share = (fixed_variable / expense_total * 100).round(2)
print("\nFixed/Variable share (%):")
print(fixed_variable_share.astype(str) + "%")

fixed_variable.to_csv(OUTPUT_DIR / "fixed_vs_variable.csv")

# =========================
# 7) Weekend vs Weekday spending
# =========================
daily_expense = (
    df[df["type"] == "expense"]
    .groupby(["date", "is_weekend"])["amount"]
    .sum()
    .reset_index()
)

weekend_stats = daily_expense.groupby("is_weekend")["amount"].agg(["mean", "median", "sum", "count"])
print("\n===== WEEKEND vs WEEKDAY (DAILY EXPENSE) =====")
print(weekend_stats)

weekend_stats.to_csv(OUTPUT_DIR / "weekend_weekday_stats.csv")

# =========================
# 8) Merchant analysis
# =========================
merchant_expense = (
    df[df["type"] == "expense"]
    .groupby("merchant")["amount"]
    .sum()
    .sort_values(ascending=False)
)
print("\n===== EXPENSE BY MERCHANT (Top 15) =====")
print(merchant_expense.head(15))

merchant_expense.head(30).to_csv(OUTPUT_DIR / "expense_by_merchant_top30.csv")

# =========================
# 9) Category MoM contribution (driver analysis)
# =========================
cat_month = (
    df[df["type"] == "expense"]
    .groupby(["month", "category_group"])["amount"]
    .sum()
    .unstack(fill_value=0)
    .sort_index()
)

cat_mom = cat_month.diff()
print("\n===== CATEGORY MoM CHANGE (latest month vs previous) =====")
if len(cat_mom) >= 2:
    latest = cat_mom.iloc[-1].sort_values(ascending=False)
    print(latest.head(10))
    latest.to_csv(OUTPUT_DIR / "category_mom_change_latest.csv")
else:
    print("Not enough months to compute MoM category contribution.")

cat_month.to_csv(OUTPUT_DIR / "category_month_matrix.csv")

# =========================
# 10) Charts
# =========================
# 10.1 Income vs Expense trend
plt.figure()
monthly_summary["income"].plot(label="Income")
monthly_summary["expense"].plot(label="Expense")
plt.title("Monthly Income vs Expense")
plt.ylabel("Amount")
plt.legend()
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "monthly_income_expense.png", dpi=160)
plt.show()

# 10.2 Saving rate trend
plt.figure()
(monthly_summary["saving_rate"] * 100).plot(marker="o")
plt.title("Monthly Saving Rate (%)")
plt.ylabel("Saving Rate (%)")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "monthly_saving_rate.png", dpi=160)
plt.show()

# 10.3 Category expense bar (top 10)
plt.figure()
category_expense.head(10).plot(kind="bar")
plt.title("Top 10 Expense Categories")
plt.ylabel("Amount")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "expense_by_category_top10.png", dpi=160)
plt.show()

# 10.4 Fixed vs Variable bar
plt.figure()
fixed_variable.plot(kind="bar")
plt.title("Fixed vs Variable Expense")
plt.ylabel("Amount")
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "fixed_vs_variable.png", dpi=160)
plt.show()

print("\n✅ Outputs saved to /outputs:")
print("- monthly_summary.csv")
print("- expense_by_category.csv")
print("- fixed_vs_variable.csv")
print("- weekend_weekday_stats.csv")
print("- expense_by_merchant_top30.csv")
print("- category_month_matrix.csv")
print("- charts: *.png")