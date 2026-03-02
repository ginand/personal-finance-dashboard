# Personal Finance Dashboard (3-Month Analysis)

A Python (Pandas) analytics project that simulates and analyzes 3 months of personal finance transactions to understand spending patterns, saving rate trends, cost structure (fixed vs variable), and key drivers of month-over-month (MoM) expense changes.

## Project Goals
- Track income, expense, saving, and saving rate over time
- Identify top spending categories and merchants
- Break down spending into fixed vs variable costs
- Explain MoM expense changes using driver analysis
- Provide actionable recommendations to improve saving rate

## Dataset
- Input: `data/transactions_3months.csv` (generated)
- Each row is a transaction with:
  - `date`, `description`, `merchant`, `category`, `amount`, `type`, `payment_method`

### Assumptions
- `amount` is always positive
- `type` determines direction: `income` vs `expense`
- Food is grouped from `Food_home` + `Food_out` into `Food`

## KPIs Defined
- **Total income** = sum(amount) where type = income
- **Total expense** = sum(amount) where type = expense
- **Saving** = income - expense
- **Saving rate** = saving / income
- **MoM expense change** = current_month_expense - previous_month_expense

## Key Findings (from latest run)
- Total income: **45,000,000**
- Total expense: **33,831,734**
- Saving rate (3-month avg): **24.82%**
- Expense trend: Feb decreased **-5.0% MoM**, Mar increased **+7.2% MoM**
- Category share:
  - **Food: 39.15%** (largest driver)
  - **Rent: 26.6%**
  - Entertainment: 10.26%, Transport: 9.21%, Utilities: 7.42%
- Cost structure: **Variable 63.32%** vs **Fixed 36.68%**
- Mar expense increase was driven mainly by:
  - Food **(+489,920)** and Shopping **(+480,444)**, offset by Entertainment **(-390,939)**
  <img width="806" height="687" alt="image" src="https://github.com/user-attachments/assets/05047a67-9e28-42a2-bc8b-c623dd360204" />
<img width="795" height="682" alt="image" src="https://github.com/user-attachments/assets/4e043243-9816-41fb-b0b8-04fff20782f2" />
<img width="797" height="686" alt="image" src="https://github.com/user-attachments/assets/4291113b-6271-457c-b55a-2ec79328e392" />
<img width="797" height="684" alt="image" src="https://github.com/user-attachments/assets/e6979233-57c4-4548-98b0-805e95ec06f3" />

## Recommendations
- Reduce Food spending by 10–15% (largest variable cost driver) to lift saving rate toward ~30%
- Set a monthly budget cap for Shopping to avoid spikes (Mar showed significant increase)
- Separate weekday vs weekend routines: weekday spending is higher due to commuting + eating out

## How to Run
```bash




pip install -r requirements.txt
python src/generate_transactions.py
python src/analysis.py
