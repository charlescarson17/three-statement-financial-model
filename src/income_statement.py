#Income statement module for the three statement model
"""
Builds the driver-based P&L:
    Volume * ASP -> Revenue -> COGS -> Gross Profit ->
    SG&A / R&D -> EBIDTA -> D&A -> EBIT -> Interest ->
    Pretax Income -> Taxes -> Net Income.

Revenue is built as a calculation from volume and average
selling price (ASP) rather than a blended growth rate so that
unit growth and pricing trends can be analyzed separately.

Interest expense is accepted as an optional input (defaults to zero)
becuase it depend on the debt schedule, which depends on cash flow, 
which depends on net income from this statement. This circular
dependency is resolved later in the debt schedule.
"""

import pandas as pd
from src.drivers import build_driver_frame, PERIODS


LINE_ITEMS =[
    "Volume", "ASP", "Revenue", "COGS", "Gross Profit",
    "SG&A", "R&D", "EBITDA", "D&A", "EBIT",
    "Interest Expense", "Pretax Income", "Tax Expense",
    "Net Income",
]


def build_income_statement(drivers, periods=PERIODS, interest_expense=None):
    """
    Build the income statement as a DataFrame (line items as rows,
    periods as columns) driven by the 'drivers' DataFrame from the drivers.py
    file.

    drivers: DataFrame from driver_build_frame()
    periods: ordered list of period labels, anchor year first
    interest expense: optional dict of {period: value}; defaults to zero
        for every period until the debt schedule feeds a real value
    """
    is_df = pd.DataFrame(index=LINE_ITEMS, columns=periods, dtype=float)

    for i, period in enumerate(periods):
        if i == 0:
            #Anchor year: volume and ASP come directly from base level
            volume = drivers.loc["base_volume", period]
            asp = drivers.loc["base_asp", period]
        else:
            prior = periods[i-1]
            volume = is_df.loc["Volume", prior] * (1 + drivers.loc["volume_growth", period])
            asp = is_df.loc["ASP", prior] * (1 + drivers.loc["asp_growth", period])
        
        revenue = volume * asp
        cogs = revenue * drivers.loc["cogs_pct_revenue", period]
        gross_profit = revenue - cogs
        sga = revenue * drivers.loc["sga_pct_revenue", period]
        rd = revenue * drivers.loc["rd_pct_revenue", period]
        ebitda = gross_profit - sga - rd
        da = revenue * drivers.loc["da_pct_revenue", period]
        ebit = ebitda - da

        int_exp = interest_expense[period] if interest_expense and period in interest_expense else 0.0

        pretax_income = ebit - int_exp
        tax_expense = pretax_income * drivers.loc["tax_rate", period]
        net_income = pretax_income - tax_expense

        is_df[period] = [
            volume, asp, revenue, cogs, gross_profit,
            sga, rd, ebitda, da, ebit,
            int_exp, pretax_income, tax_expense, net_income,
        ]

    return is_df


#Main test
if __name__ == "__main__":
    #Quick manual check: build drivers and then run P&L
    #No debt yet
    drivers = build_driver_frame()
    income_statement = build_income_statement(drivers)
    print(income_statement.round(2))