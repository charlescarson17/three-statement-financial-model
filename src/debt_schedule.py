#Debt schedule module for three statement model
"""
Builds the term loan and revolver rollforward: beginning balance,
scheduled term loan amortization, revolver draws & paydowns driven by
a cash-sweep mechanism, interest expense on both debt instruments, and
the resulting ending cash position.

Cash Sweep Logic: 
For each forecast period, the cash available before revolver activity is
calculated as: beginning cash + cash from from operations + cash flow from
investing - term loan amortization - dividends. If that falls below the
min_cash_target driver, the revolver automatically draws enough to cover the
shortfall. If it exceed the target and revolver balance exists, excess cash 
automactially repays the revolver at an amount capped at the outstanding balance.

Circularity Note:
Interest expense is calculated on the Beginning balance of each debt instrument,
which avoids a circular reference for now but is a simplification. Net Income
(which depends on Interest Expense) is what drives the cash sweep. This is intentional
staging. Phase 5 replaces this measure with the average balance method or interative 
convergence once the full pipeline runs end to end. Anchor year (first period) is treated
as an actual balance. It is not forecasted and also has no draw downs, paydowns, or sweep
logic applied.
"""

import pandas as pd
from src.drivers import build_driver_frame, PERIODS
from src.income_statement import build_income_statement
from src. working_capital import build_working_capital

LINE_ITEMS = [
    "Beginning Cash",
    "Beginning Term Loan", "Term Load Paydown", "Ending Term Loan",
    "Beginning Revolver", "Revolver Draw/(Paydown)", "Ending Revolver",
    "Interest Expense - Term Loan", "Interest Expense - Revolver",
    "Total Interest Expense",
    "Ending Cash",
]


def build_debt_schedule(
        drivers,
        income_statement,
        working_capital,
        periods=PERIODS,
        beginning_cash=10.0,
        beginning_term_loan=200.0,
        beginning_revolver=0.0,
):
    """
    Build the debt schedule as a DataFrame.
    (line items as rows, periods as columns)

    drivers: DataFrame from build_driver_frame()
    income_statement: DataFrame from build_income_statement()
    working_capital: DataFrame from build_working_capital()
    periods: ordered list of period labels, anchor year first
    beginning_cash / beginning_term_loan / beginning_revolver: opening 
        balances as of the start of the anchor year
    """
    debt_df = pd.DataFrame(index=LINE_ITEMS, columns=periods, dtype=float)

    for i, period in enumerate(periods):
        if i == 0:
            #Anchor year; treat as actual, no forecasting
            beg_cash = beginning_cash
            beg_term_loan = beginning_term_loan
            beg_revolver = beginning_revolver

            term_loan_paydown = 0.0
            ending_term_loan = beg_term_loan
            revolver_change = 0.0
            ending_revolver = beg_revolver
            ending_cash = beg_cash
        else:
            prior = periods[i-1]
            beg_cash = debt_df.loc["Ending Cash", prior]
            beg_term_loan = debt_df.loc["Ending Term Loan", prior]
            beg_revolver = debt_df.loc["Ending Revolver", prior]

            revenue = income_statement.loc["Revenue", period]
            net_income = income_statement.loc["Net Income", period]
            da = income_statement.loc["D&A", period]
            change_ar = working_capital.loc["Change in AR", period]
            change_inventory = working_capital.loc["Change in Inventory", period]
            change_ap = working_capital.loc["Change in AP", period]
            capex = revenue * drivers.loc["capex_pct_revenue", period]
            dividends = max(net_income, 0.0) * drivers.loc["dividend_payout_pct", period]

            cfo = net_income + da -change_ar - change_inventory + change_ap
            cfi = -capex

            term_loan_paydown = min(
                beg_term_loan * drivers.loc["term_loan_amort_pct", period],
                beg_term_loan,
            )
            ending_term_loan = beg_term_loan - term_loan_paydown

            cash_before_revolver = beg_cash + cfo + cfi - term_loan_paydown - dividends
            min_cash = drivers.loc["min_cash_target", period]

            if cash_before_revolver < min_cash:
                revolver_draw = min_cash - cash_before_revolver
                revolver_paydown = 0.0
            else:
                excess_cash = cash_before_revolver - min_cash
                revolver_paydown = min(excess_cash, beg_revolver)
                revolver_draw = 0.0

            revolver_change = revolver_draw - revolver_paydown
            ending_revolver = beg_revolver + revolver_change
            ending_cash = cash_before_revolver + revolver_change
        
        #Interest on beginning balances -- see circularity note
        interest_term_loan = beg_term_loan * drivers.loc["interest_rate_term_loan", period]
        interest_revolver = beg_revolver * drivers.loc["interest_rate_revolver", period]
        total_interest = interest_term_loan + interest_revolver

        debt_df[period] = [
            beg_cash,
            beg_term_loan, term_loan_paydown, ending_term_loan,
            beg_revolver, revolver_change, ending_revolver,
            interest_term_loan, interest_revolver, total_interest,
            ending_cash,
        ]

    return debt_df


#Test Main
if __name__ == "__main__":
    #Quick manual check
    #Build the full chain up through debt schedule
    #Use zero interest expense in the income statement
    drivers = build_driver_frame()
    income_statement = build_income_statement(drivers)
    working_capital = build_working_capital(drivers, income_statement)
    debt_schedule = build_debt_schedule(drivers, income_statement, working_capital)
    print(debt_schedule.round(2))

