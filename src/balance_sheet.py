#Balance sheet module for the three-statement model
"""
Assembles the balance sheet from every upstream modules. Cash and
debt balance from the debt schedule. AR, Inventory, and AP from the
working capital schedule. Commonn Stock and Retained Earnings form the 
equity schedule. Revenue and D&A from the income statement.

Builds the P&E rollforward directly. Gross P&E grows each period by CAPEX.
Accumulated D&A grows each period by that period's D&A expense from the 
income statement. 
PP&E: Net = Gross - Accumulated D&A

Simplificaiation: Other Current Assets and Accured Liabiliites are held flat
at their acnhor year level since driver.py does not yet define growth 
assumptions for either.

Includes an auto-balancing check. Total Assets should equal Toal Liabilities
+ Total Equity in every period, with a small rounding tolerance.
"""

import pandas as pd
from src.drivers import build_driver_frame, PERIODS
from src.income_statement import build_income_statement
from src.working_capital import build_working_capital
from src.debt_schedule import build_debt_schedule
from src.equity_schedule import build_equity_schedule
from src.opening_balances import OPENING_BALANCES, compute_retained_earnings_plug

LINE_ITEMS = [
    "Cash", "Accounts Receivable", "Inventory", "Other Current Assets", "Total Current Assets",
    "PP&E, Gross", "Accumulated D&A", "PP&E Net", "Total Assets",
    "Accounts Payable", "Accrued Liabilities", "Revolver", "Total Current Liabilities",
    "Term Loan", "Total Liabilities",
    "Common Stock", "Retained Earnings", "Total Equity",
    "Total Liabilities & Equity", "Balance Check",
]


def build_balance_sheet(
        drivers,
        income_statement,
        working_capital,
        debt_schedule,
        equity_schedule,
        periods=PERIODS,
):
    """
    Build the balance sheet as a DataFrame, assembled from every upstream module
    (line items as rows, periods as columns)

    drivers / income_statement / working_capital / debt_schedule / equity schedule:
        Dataframes from their respective build functions
    periods: ordered list of period labels, anchor year first
    beginning_other_current_assets / beginning_accrued_liabilities / 
        beginning_ppe_gross / beginning_accumulated_da: opening balances
        as of the start of the year
    """
    bs_df = pd.DataFrame(index=LINE_ITEMS, columns=periods, dtype=float)

    for i, period in enumerate(periods):
        if i == 0:
            #Anchor year treated as actual, no forecasting
            other_ca = OPENING_BALANCES["other_current_assets"]
            accrued_liab = OPENING_BALANCES["accrued_liabilities"]
            ppe_gross = OPENING_BALANCES["ppe_gross"]
            accumulated_da = OPENING_BALANCES["accumulated_da"]
        else:
            prior = periods[i-1]
            #Flat projections
            other_ca = bs_df.loc["Other Current Assets", prior]
            accrued_liab = bs_df.loc["Accrued Liabilities", prior]

            revenue = income_statement.loc["Revenue", period]
            capex = revenue * drivers.loc["capex_pct_revenue", period]
            da = income_statement.loc["D&A", period]

            ppe_gross = bs_df.loc["PP&E, Gross", prior] + capex
            accumulated_da = bs_df.loc["Accumulated D&A", prior] + da

        ppe_net = ppe_gross - accumulated_da

        cash = debt_schedule.loc["Ending Cash", period]
        ar = working_capital.loc["Accounts Receivable", period]
        inventory = working_capital.loc["Inventory", period]
        total_current_assets = cash + ar + inventory + other_ca
        total_assets = total_current_assets + ppe_net

        ap = working_capital.loc["Accounts Payable", period]
        revolver = debt_schedule.loc["Ending Revolver", period]
        total_current_liabilities = ap + accrued_liab + revolver
        term_loan = debt_schedule.loc["Ending Term Loan", period]
        total_liabilities = total_current_liabilities + term_loan

        common_stock = equity_schedule.loc["Ending Common Stock", period]
        retained_earnings = equity_schedule.loc["Ending Retained Earnings", period]
        total_equity = common_stock + retained_earnings

        total_liabilities_equity = total_liabilities + total_equity
        balance_check = total_assets - total_liabilities_equity

        bs_df[period] = [
            cash, ar, inventory, other_ca, total_current_assets,
            ppe_gross, accumulated_da, ppe_net, total_assets,
            ap, accrued_liab, revolver, total_current_liabilities,
            term_loan, total_liabilities,
            common_stock, retained_earnings, total_equity,
            total_liabilities_equity, balance_check
        ]

    return bs_df


def check_balance_sheet_balances(balance_sheet, tolerance=0.01):
    """
    Verify Total Assets == Total Liabilities + Total Equity for every period within
    a small rounding tolerance. Raises an AssertionError naming specific period and 
    imbalance amount if any period falls outside of tolerance.
    """
    for period in balance_sheet.columns:
        imbalance = balance_sheet.loc["Balance Check", period]
        assert abs(imbalance) < tolerance, (
            f"Balance sheet does not balance in {period}: "
            f"Imbalanced by {imbalance: 4f}"
        )
    print("Balance Check: PASS for all periods")


#Test Main
if __name__ == "__main__":
    #Quick manual check
    #Build the full chain and balance sheet
    #Confirm it balances in every period
    drivers = build_driver_frame()
    income_statement = build_income_statement(drivers)
    working_capital = build_working_capital(drivers, income_statement)
    debt_schedule = build_debt_schedule(drivers, income_statement, working_capital)
    
    retained_earnings_plug = compute_retained_earnings_plug(
        working_capital, debt_schedule, PERIODS
    )

    equity_schedule = build_equity_schedule(
        drivers, income_statement, beginning_retained_earnings=retained_earnings_plug
    )

    balance_sheet = build_balance_sheet(
        drivers, income_statement, working_capital, debt_schedule, equity_schedule
    )
    print(balance_sheet.round(2))
    check_balance_sheet_balances(balance_sheet)