#Cash flow statement module for the three statement model
"""
Independently rebuilds the standard CFO, CFI, and CFF structure from 
the income statement, working capital schedule, debt schedule, and equity
schedule.

CFO = Net Income + DA - Change in AR - Chaing in Inventory + Change in AP
CFI = -Capex
CFF = -Term Loan Payment + Revolver Draw/(Paydown) - Dividends + Common Stock Issuance

Includes tie-out check with Ending Cash calculated in the debt schedule.

Anchor year is treated as an actual, not forecasted.
"""

import pandas as pd
from src.drivers import build_driver_frame, PERIODS
from src.income_statement import build_income_statement
from src.working_capital import build_working_capital
from src.debt_schedule import build_debt_schedule
from src.equity_schedule import build_equity_schedule
from src.opening_balances import OPENING_BALANCES, compute_retained_earnings_plug

LINE_ITEMS = [
    "Net Income", "D&A", "Change in AR", "Change in Inventory", "Change in AP",
    "Cash Flow from Operations",
    "Capex",
    "Cash Flow from Investing",
    "Term Loan Paydown", "Revolver Draw / (Paydown)", "Dividends", "Common Stock Issuance",
    "Cash Flow from Financing",
    "Net Change in Cash", "Beginning Cash", "Ending Cash",
    "Cash Tie-Out Check",
]


def build_cash_flow_statement(
        drivers,
        income_statement,
        working_capital,
        debt_schedule,
        equity_schedule,
        periods=PERIODS,
):
    """
    Build the cash flow statement as a DataFrame
    (line items as rows, periods as columns)

    drivers / income_statement / working_capital /debt_schedule /
        equity_schedule: DataFrames from their respective build functions
    periods: ordered list of period labels, anchor year first
    beginning_cash: opening cash balance as of the start of the anchor year
    """
    cf_df = pd.DataFrame(index=LINE_ITEMS, columns=periods, dtype=float)

    for i, period in enumerate(periods):
        if i == 0:
            #Anchor year; treat as actual, no cash flow activity
            net_income = 0.0
            da = 0.0
            change_ar = 0.0
            change_inventory = 0.0
            change_ap = 0.0
            cfo = 0.0
            capex = 0.0
            cfi = 0.0
            term_loan_paydown = 0.0
            revolver_change = 0.0
            dividends = 0.0
            common_stock_issuance = 0.0
            cff = 0.0
            net_change_in_cash = 0.0
            beg_cash = OPENING_BALANCES["cash"]
            ending_cash = OPENING_BALANCES["cash"]
        else:
            prior = periods[i-1]
            net_income = income_statement.loc["Net Income", period]
            da = income_statement.loc["D&A", period]
            change_ar = working_capital.loc["Change in AR", period]
            change_inventory = working_capital.loc["Change in Inventory", period]
            change_ap = working_capital.loc["Change in AP", period]
            cfo = net_income + da - change_ar - change_inventory + change_ap

            revenue = income_statement.loc["Revenue", period]
            capex = revenue * drivers.loc["capex_pct_revenue", period]
            cfi = -capex

            term_loan_paydown = debt_schedule.loc["Term Loan Paydown", period]
            revolver_change = debt_schedule.loc["Revolver Draw/(Paydown)", period]
            dividends = equity_schedule.loc["Dividends", period]
            common_stock_issuance = equity_schedule.loc["Common Stock Issuance", period]
            cff = -term_loan_paydown + revolver_change - dividends + common_stock_issuance

            net_change_in_cash = cfo + cfi + cff
            beg_cash = cf_df.loc["Ending Cash", prior]
            ending_cash = beg_cash + net_change_in_cash

        debt_schedule_ending_cash = debt_schedule.loc["Ending Cash", period]
        tie_out_check = ending_cash - debt_schedule_ending_cash

        cf_df[period] = [
            net_income, da, change_ar, change_inventory, change_ap,
            cfo,
            capex,
            cfi,
            term_loan_paydown, revolver_change, dividends, common_stock_issuance,
            cff,
            net_change_in_cash, beg_cash, ending_cash,
            tie_out_check,
        ]

    return cf_df


def check_cash_flow_ties_to_debt_schedule(cash_flow_statement, tolerance=0.01):
    """
    Verify that this statement's independently calculated Ending Cash matches
    the debt schedule's ending cash for every period, within a small
    rounding tolerance.
    """
    for period in cash_flow_statement.columns:
        mismatch = cash_flow_statement.loc["Cash Tie-Out Check", period]
        assert abs(mismatch) < tolerance, (
            f"Cash flow statement does not tie out to debt schedule in {period}:"
            f"Difference of {mismatch: .4f}"
        )
    print("Cash Tie-Out Check: PASS for all periods")


#Test Main
if __name__ == "__main__":
    #Quick manual check
    #Build the full chain, assemble the cash flow statement
    #Confirm CFS ending cash ties to debt schedule
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

    cash_flow_statement = build_cash_flow_statement(
        drivers, income_statement, working_capital, debt_schedule, equity_schedule
    )
    print(cash_flow_statement.round(2))
    check_cash_flow_ties_to_debt_schedule(cash_flow_statement)
