#Working capital schedule module for the three statement model
"""
Builds Accounts Receivable, Inventory, and Accounts Payable balances
from the DSO, DIO, & DPO driver assumptions. Applied against Revenue
and COGS form the income statement.

Also computes period-over-period changes in each balance which feeds
directly into the Cash Flow from Operations section of the Cash Flow
Statement.

Formulas follow standard convention:
    AR = (DSO / 365) * Revenue
    Inventory = (DIO / 365) * COGS
    AP = (DPO / 365) * COGS
"""

import pandas as pd
from src.drivers import build_driver_frame, PERIODS
from src.income_statement import build_income_statement

DAYS_IN_YEAR = 365

LINE_ITEMS = [
    "Accounts Receivable", "Inventory", "Accounts Payable",
    "Change in AR", "Change in Inventory", "Change in AP",
]


def build_working_capital(drivers, income_statement, periods=PERIODS):
    """
    Build the working capital schedule as a DataFrame
    (line items as rows, periods as columns).

    drivers: DataFrame from build_driver_frame()
    income_statement: DataFrame from build_income_statement()
    periods: ordered list of period labels, anchor year first
    """
    wc_df = pd.DataFrame(index=LINE_ITEMS, columns=periods, dtype=float)

    for i, period in enumerate(periods):
        revenue = income_statement.loc["Revenue", period]
        cogs = income_statement.loc["COGS", period]

        ar = (drivers.loc["dso_days", period] / DAYS_IN_YEAR) * revenue
        inventory = (drivers.loc["dio_days", period] / DAYS_IN_YEAR) * cogs
        ap = (drivers.loc["dpo_days", period] / DAYS_IN_YEAR) * cogs

        if i == 0:
            #Anchor year; no prior period to compare against, so no change
            change_ar = 0.0
            change_inventory = 0.0
            change_ap = 0.0
        else:
            prior = periods[i-1]
            change_ar = ar - wc_df.loc["Accounts Receivable", prior]
            change_inventory = inventory - wc_df.loc["Inventory", prior]
            change_ap = ap - wc_df.loc["Accounts Payable", prior]
        
        wc_df[period] = [ar, inventory, ap, change_ar, change_inventory, change_ap]

    return wc_df


#Test Main
if __name__ == "__main__":
    #Quick manual check
    #Build drivers and income statement
    #Derive working capital schedule from both
    drivers = build_driver_frame()
    income_statement = build_income_statement(drivers)
    working_capital = build_working_capital(drivers, income_statement)
    print(working_capital.round(2))
