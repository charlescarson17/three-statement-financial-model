#Entry point for the three statement model
"""
Runs the full three statement model via run_three_statement_model().
Prints the income statment, balance sheet, and cash flow statement. 
Confirms both the balance check and cash flow tie-out check pass.

This is the single command a user runs to see the whole model.
"""
from src.model_runner import run_three_statement_model
from src.balance_sheet import check_balance_sheet_balances
from src.cash_flow import check_cash_flow_ties_to_debt_schedule

if __name__ == "__main__":
    results = run_three_statement_model()

    print(results["income_statement"].round(2))
    print(results["balance_sheet"].round(2))
    print(results["cash_flow_statement"].round(2))

    check_balance_sheet_balances(results["balance_sheet"])
    check_cash_flow_ties_to_debt_schedule(results["cash_flow_statement"])
    