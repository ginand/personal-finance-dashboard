import random
from datetime import date, timedelta
import csv
from pathlib import Path

random.seed(42)

OUT = Path("data/transactions_3months.csv")
OUT.parent.mkdir(exist_ok=True)

start = date(2026, 1, 1)
end = date(2026, 3, 31)

# ===== Assumptions (m có thể chỉnh) =====
salary_amount = 15_000_000
rent_amount = 3_000_000

# Utilities & subscriptions
internet_amount = 250_000
mobile_amount = 100_000
utilities_base = 450_000  # điện/nước trung bình
gym_amount = 300_000      # optional

# Transport
# trung bình 1-2 chuyến/ngày, không phải ngày nào cũng đi grab
grab_trip_range = (25_000, 60_000)
bus_day_cost = 15_000

# Food costs
# ăn ở nhà: rẻ hơn (chia theo bữa)
home_meal_range = (20_000, 45_000)
# ăn ngoài: đắt hơn
out_meal_range = (35_000, 90_000)

# Probabilities: (có thể chỉnh theo lifestyle)
# breakfast: 60% ăn ngoài, lunch: 75% ăn ngoài, dinner: 40% ăn ngoài (tối hay nấu)
p_out = {"breakfast": 0.60, "lunch": 0.75, "dinner": 0.40}

# Coffee / snacks
p_coffee = 0.35
coffee_range = (18_000, 55_000)

# Entertainment weekly
p_entertainment_weekend = 0.55
entertainment_range = (60_000, 250_000)

# Shopping occasional
p_shopping_week = 0.18
shopping_range = (120_000, 1_200_000)

# Health occasional
p_health_month = 0.20
health_range = (80_000, 600_000)

merchants_food_out = ["GrabFood", "ShopeeFood", "Canteen", "Local Restaurant", "Highlands", "Phuc Long"]
merchants_food_home = ["WinMart", "Co.opmart", "Bach Hoa Xanh", "Local Market"]
merchants_transport = ["Grab", "Bus"]
merchants_ent = ["CGV", "Karaoke", "Cafe", "Streaming"]
merchants_shop = ["Shopee", "Lazada", "Uniqlo", "Local Store"]
merchants_health = ["Pharmacy", "Clinic"]

def add_row(rows, d, desc, merchant, category, amount, t="expense", pay="card", notes=""):
    rows.append({
        "date": d.isoformat(),
        "description": desc,
        "merchant": merchant,
        "category": category,
        "amount": int(amount),
        "type": t,
        "payment_method": pay,
        "notes": notes
    })

rows = []

# ===== Generate rows =====
cur = start
while cur <= end:
    weekday = cur.weekday()  # 0=Mon ... 5=Sat 6=Sun
    is_weekend = weekday >= 5

    # Salary on 1st day each month
    if cur.day == 1:
        add_row(rows, cur, "Salary", "Company", "Income", salary_amount, t="income", pay="bank_transfer")

    # Rent on 5th day each month
    if cur.day == 5:
        add_row(rows, cur, "Rent", "Landlord", "Rent", rent_amount, pay="bank_transfer")

    # Internet on 10th
    if cur.day == 10:
        add_row(rows, cur, "Internet bill", "ISP", "Utilities", internet_amount, pay="bank_transfer")

    # Mobile on 15th
    if cur.day == 15:
        add_row(rows, cur, "Mobile plan", "Telco", "Utilities", mobile_amount, pay="bank_transfer")

    # Utilities monthly on 20th (biến động chút)
    if cur.day == 20:
        util = utilities_base + random.randint(-120_000, 180_000)
        add_row(rows, cur, "Electricity/Water", "Utility Provider", "Utilities", util, pay="bank_transfer")

    # Gym on 2nd
    if cur.day == 2:
        add_row(rows, cur, "Gym membership", "Gym", "Health", gym_amount, pay="card")

    # Meals: 3/day
    for meal in ["breakfast", "lunch", "dinner"]:
        eat_out = random.random() < p_out[meal]
        if eat_out:
            amount = random.randint(*out_meal_range)
            merchant = random.choice(merchants_food_out)
            cat = "Food_out"
            desc = f"{meal.title()} (out)"
        else:
            amount = random.randint(*home_meal_range)
            merchant = random.choice(merchants_food_home)
            cat = "Food_home"
            desc = f"{meal.title()} (home)"
        add_row(rows, cur, desc, merchant, cat, amount, pay="cash" if random.random() < 0.35 else "card")

    # Coffee/snacks sometimes
    if random.random() < p_coffee:
        add_row(
            rows, cur, "Coffee/Snack",
            random.choice(["Highlands", "Phuc Long", "Circle K", "Local Cafe"]),
            "Coffee",
            random.randint(*coffee_range),
            pay="cash" if random.random() < 0.45 else "card"
        )

    # Transport:
    # weekday: often go to work => either bus or grab
    if not is_weekend:
        if random.random() < 0.55:
            # bus day pass / 2 rides
            add_row(rows, cur, "Commute", "Bus", "Transport", bus_day_cost, pay="cash")
        else:
            # 1-2 grab trips
            trips = 1 if random.random() < 0.65 else 2
            for _ in range(trips):
                add_row(rows, cur, "Ride", "Grab", "Transport", random.randint(*grab_trip_range), pay="card")
    else:
        # weekend: fewer commuting, maybe 0-1 trip
        if random.random() < 0.55:
            add_row(rows, cur, "Ride", "Grab", "Transport", random.randint(*grab_trip_range), pay="card")

    # Entertainment on weekend
    if is_weekend and (random.random() < p_entertainment_weekend):
        add_row(
            rows, cur, "Entertainment",
            random.choice(merchants_ent),
            "Entertainment",
            random.randint(*entertainment_range),
            pay="card"
        )

    # Shopping weekly (random day)
    if random.random() < (p_shopping_week / 7):
        add_row(
            rows, cur, "Shopping",
            random.choice(merchants_shop),
            "Shopping",
            random.randint(*shopping_range),
            pay="card"
        )

    # Health monthly (random day)
    if random.random() < (p_health_month / 30):
        add_row(
            rows, cur, "Health expense",
            random.choice(merchants_health),
            "Health",
            random.randint(*health_range),
            pay="card"
        )

    cur += timedelta(days=1)

# Sort rows by date (then keep original order inside day)
rows.sort(key=lambda r: r["date"])

# Write CSV
fields = ["date", "description", "merchant", "category", "amount", "type", "payment_method", "notes"]
with OUT.open("w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

print(f"✅ Generated {len(rows)} rows -> {OUT}")
print("Tip: update analysis.py to read data/transactions_3months.csv")