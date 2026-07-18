#Equity schedule module for three statement model
"""
Builds the equity rollforward. Common stock / Additional Paid-in-Capital and
Retained Earnings which rolls forward as beginning balance + Net Income - 
Dividends each period.

Dividends are calculated the same way in the debt schedule's cash sweep
logic (net income * dividend_payout_pct) for consistency.

Anchor year is treated as an actual balance, not forecasted.
"""

import pandas as pd
from src.drivers import build_driver_frame, PERIODS
from src.income_statement import build_income_statement
from src.working_capital import build_working_capital
from src.debt_schedule import build_debt_schedule
from src.opening_balances import OPENING_BALANCES, compute_retained_earnings_plug

LINE_ITEMS = [
    "Beginning Common Stock", "Common Stock Issuance", "Ending Common Stock",
    "Beginning Retained Earnings", "Net Income", "Dividends", "Ending Retained Earnings",
    "Total Equity",
]


def build_equity_schedule(
        drivers,
        income_statement,
        beginning_retained_earnings,
        periods=PERIODS,
):
    """
    Build the equity schedule as a DataFrame
    (line items as rows, periods as columns)

    drivers: DataFrame from build_driver_frame()
    income_statement: DataFrame from build_income_statement()
    periods: ordered list of period labels; anchor year first
    beginning_common_stock /  beginning_retained_earnings: opening
        balances as of the start of the anchor year
    """
    equity_df = pd.DataFrame(index=LINE_ITEMS, columns=periods, dtype=float)

    for i, period in enumerate(periods):
        if i == 0:
            #Anchor year; treat as actual, no forecasting
            beg_common_stock = OPENING_BALANCES["common_stock"]
            common_stock_issuance = 0.0
            ending_common_stock = beg_common_stock

            beg_retained_earnings = beginning_retained_earnings
            net_income = 0.0
            dividends = 0.0
            ending_retained_earnings = beg_retained_earnings
        else:
            prior = periods[i-1]
            beg_common_stock = equity_df.loc["Ending Common Stock", prior]
            common_stock_issuance = 0.0   #no issuance driver yet
            ending_common_stock = beg_common_stock + common_stock_issuance

            beg_retained_earnings = equity_df.loc["Ending Retained Earnings", prior]
            net_income = income_statement.loc["Net Income", period]
            dividends = max(net_income, 0.0) * drivers.loc["dividend_payout_pct", period]
            ending_retained_earnings = beg_retained_earnings + net_income - dividends

        total_equity = ending_common_stock + ending_retained_earnings

        equity_df[period] = [
            beg_common_stock, common_stock_issuance, ending_common_stock,
            beg_retained_earnings, net_income, dividends, ending_retained_earnings,
            total_equity,
        ]

    return equity_df


#Test Main
if __name__ == "__main__":
    #Quick manual check
    #Build the chain through income statement
    #Derive the equity schedule from it
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
    print(equity_schedule.round(2))

