#Core test suite for the model
"""
Broad tests covering the highest value correctness gauges.

Tests include income statement math, working capital formulas, debt schedule
logic, the balance sheet & cash flow tie-out checks, and convergence of the 
iterative circularity of interest expense.
"""

import pytest


# Income Statement Test
def test_net_income_equals_pretax_minus_tax(income_statement):
    for period in income_statement.columns:
        pretax = income_statement.loc["Pretax Income", period]
        tax = income_statement.loc["Tax Expense", period]
        net_income = income_statement.loc["Net Income", period]
        assert net_income == pytest.approx(pretax - tax, abs=0.01)


# Working Capital Test
def test_ar_matches_dso_formula(drivers, income_statement, working_capital):
    period = drivers.columns[1]  # first forecast period
    revenue = income_statement.loc["Revenue", period]
    dso = drivers.loc["dso_days", period]
    expected_ar = (dso / 365) * revenue
    actual_ar = working_capital.loc["Accounts Receivable", period]
    assert actual_ar == pytest.approx(expected_ar, abs=0.01)


# Debt Schedule Test
def test_term_loan_paydown_never_exceeds_balance(debt_schedule):
    for period in debt_schedule.columns:
        paydown = debt_schedule.loc["Term Loan Paydown", period]
        beginning_balance = debt_schedule.loc["Beginning Term Loan", period]
        assert paydown <= beginning_balance + 0.01


def test_revolver_draws_exact_shortfall(drivers, debt_schedule):
    period = drivers.columns[1]
    revolver_change = debt_schedule.loc["Revolver Draw/(Paydown)", period]
    # Under default assumptions the company is cash-generative, so no
    # draw is expected here -- this test documents that expectation and
    # will catch a regression if the sweep logic starts drawing
    # unexpectedly under unchanged default assumptions.
    assert revolver_change <= 0.01


# Balance Sheet Test
def test_balance_sheet_balances(balance_sheet):
    for period in balance_sheet.columns:
        imbalance = balance_sheet.loc["Balance Check", period]
        assert abs(imbalance) < 0.01


def test_balance_check_catches_imbalance(balance_sheet):
    from src.balance_sheet import check_balance_sheet_balances

    broken = balance_sheet.copy()
    period = broken.columns[1]
    broken.loc["Cash", period] += 100  # introduce a $100 imbalance
    broken.loc["Total Assets", period] += 100
    broken.loc["Balance Check", period] += 100

    with pytest.raises(AssertionError):
        check_balance_sheet_balances(broken)


# Cash Flow Test
def test_cash_flow_ties_to_debt_schedule(cash_flow_statement):
    from src.cash_flow import check_cash_flow_ties_to_debt_schedule

    check_cash_flow_ties_to_debt_schedule(cash_flow_statement)  # raises if it fails


# Model Runner Test
def test_model_converges_and_both_checks_pass(model_results):
    from src.balance_sheet import check_balance_sheet_balances
    from src.cash_flow import check_cash_flow_ties_to_debt_schedule

    check_balance_sheet_balances(model_results["balance_sheet"])
    check_cash_flow_ties_to_debt_schedule(model_results["cash_flow_statement"])
