#Opening balances module for the three statement model
"""
Single source of truth for every anchor year (opening) balance sheet
assumption used across the model:
    Cash
    Term Loan
    Revolver
    Common Stock
    Other Current Assets
    Accrued Liabilities
    PP&E (gross and accumulated D&A)

Every module that needs an anchor year value reads from
OPENING_BALANCES here rather than accepting its own default or
module specific arguments. This creates a single entry point for 
balance data and syncronizes across the model.

Also owns compute_retained_earnings_plug() so the anchor year balance
sheet is balanced and defined in one place.
"""

OPENING_BALANCES = {
    "cash": 10.0,
    "term_loan": 200.0,
    "revolver": 0.0,
    "common_stock": 50.0,
    "other_current_assets": 15.0,
    "accrued_liabilities": 12.0,
    "ppe_gross": 300.0,
    "accumulated_da": 50.0,
}


def compute_retained_earnings_plug(working_capital, debt_schedule, periods):
    """
    Back into the retained earnings figure for the anchor year's balance sheet to balance
    exactly, given every other opening balance assumptions. 
    
    Standard modeling technique: whena full historical balance sheet isn't available, retained
    earnings is the customary plug since it represents the cumulative effect of all the prior years'
    undistributed earnings and is the natural account to absorb whatever is needed to make the balance
    sheet's opening year balance.

    working_capital: DataFrame from working capital module
    debt_schedule: DataFrame from debt schedule module
    periods: ordered list of period labels, anchor year first
    """
    anchor = periods[0]
    ppe_net = OPENING_BALANCES["ppe_gross"] - OPENING_BALANCES["accumulated_da"]

    total_assets = (
        OPENING_BALANCES["cash"]
        + working_capital.loc["Accounts Receivable", anchor]
        + working_capital.loc["Inventory", anchor]
        + OPENING_BALANCES["other_current_assets"]
        + ppe_net
    )
    total_liabilities = (
        working_capital.loc["Accounts Payable", anchor]
        + OPENING_BALANCES["accrued_liabilities"]
        + debt_schedule.loc["Ending Revolver", anchor]
        + debt_schedule.loc["Ending Term Loan", anchor]
    )
    return total_assets - total_liabilities - OPENING_BALANCES["common_stock"]
