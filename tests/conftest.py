#Shared pytest fixtures for the three statement model tests
"""
Builds model pipeline once per test so individual tests
only need to request the specific fixtures they need
rather than re-running all/any upstream pipeline modules.
"""

import pytest
from src.drivers import build_driver_frame
from src.income_statement import build_income_statement
from src.working_capital import build_working_capital
from src.debt_schedule import build_debt_schedule
from src.equity_schedule import build_equity_schedule
from src.balance_sheet import build_balance_sheet
from src.cash_flow import build_cash_flow_statement
from src.opening_balances import compute_retained_earnings_plug
from src.model_runner import run_three_statement_model


@pytest.fixture
def drivers():
    return build_driver_frame()


@pytest.fixture
def income_statement(drivers):
    return build_income_statement(drivers)


@pytest.fixture
def working_capital(drivers, income_statement):
    return build_working_capital(drivers, income_statement)


@pytest.fixture
def debt_schedule(drivers, income_statement, working_capital):
    return build_debt_schedule(drivers, income_statement, working_capital)


@pytest.fixture
def equity_schedule(drivers, income_statement, working_capital, debt_schedule):
    retained_earnings_plug = compute_retained_earnings_plug(
        working_capital, debt_schedule, drivers.columns.tolist()
    )
    return build_equity_schedule(
        drivers, income_statement, beginning_retained_earnings=retained_earnings_plug
    )


@pytest.fixture
def balance_sheet(drivers, income_statement, working_capital, debt_schedule, equity_schedule):
    return build_balance_sheet(
        drivers, income_statement, working_capital, debt_schedule, equity_schedule
    )


@pytest.fixture
def cash_flow_statement(drivers, income_statement, working_capital, debt_schedule, equity_schedule):
    return build_cash_flow_statement(
        drivers, income_statement, working_capital, debt_schedule, equity_schedule
    )


@pytest.fixture
def model_results():
    return run_three_statement_model()