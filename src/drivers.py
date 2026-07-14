#Driver assumptions module for the three-statement model

"""
Defines the forecast periods and the full set of input assumptions
(drivers) that power the model. 

Revenue built from volume X ASP, cost ratios as % of revenue, working capital days,
debt/interest rates, and cash sweep/dividend policy.

Provides build_driver_frame() to create a DataFrame (drivers as rows,
periods as columns) from defaults with optional per-period overrides.
"""

import pandas as pd

periods = ["2025A", "2026E", "2027E", "2028E", "2029E"]

default_drivers ={
    "base_volume": 1_000_000,   #units, 2025A
    "base_asp": 100.0,          #$ per unit
    "volume_growth": 0.05,
    "asp_growth": 0.03,
    "cogs_pct_revenue": 0.45,
    "sga_pct_revenue": 0.20,
    "rd_pct_revenue": 0.05,
    "da_pct_revenue": 0.03,
    "capex_pct_revenue": 0.04,
    "tax_rate": 0.25,
    "dso_days": 45,
    "dio_days": 60,
    "dpo_days": 40,
    "interest_rate_revolver": 0.07,
    "interest_rate_term_loan": 0.05,
    "min_cash_target": 10.0,
    "term_loan_amort_pct": 0.10,
    "dividend_payout_pct": 0.0,
}

def build_driver_frame(period=periods, overrides=None):
    """
    Build a DataFrame. One row per driver. One column per period.
    Flat-seeded from default_drivers with optional per period
    overrides for ramping or decay of assumptions.
    
    overrides: dict of {driver_name: {period: value}}
        ex: {"volume_growth": {"2027E": 0.04, "2028E": 0.03}}
    """
    df = pd.DataFrame({period: default_drivers for period in periods})
    df.index.name = "driver"
    df.columns.name = "period"

    if overrides:
        for driver, period_overrides in overrides.items():
            for period, value in period_overrides.items():
                df.loc[driver, period] = value
    
    return df


#Main test
if __name__ == "__main__":
    #Quick manual check: flat drivers, plus an example ramp on volume
    drivers = build_driver_frame(
        overrides={"volume_growth": {"2027E": 0.04, "2028E": 0.03, "2029E": 0.02}}
    )
    print(drivers)