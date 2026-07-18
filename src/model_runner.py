#Model runner module for the three statement model
"""
Orchetrates teh full pipelien and resolves the
interest expense circularity via iterative convergence.
Interest expense depends on debt balance, which depends
on cash sweep, which depends on net income, which depends
on interest expense.

Each iteration reruns the income statement using the debt
schedule's interest expense from the prior iteration. Then
reruns the debt schedule and compares the newly calculated 
interest expense against the former. Convergence is considered
successful once overy period's interest expense change from one 
interation to the next is less than a defined tolerance.

This is similar to how Excel's iterative calculation mode 
resolves circular references.
"""
from src.drivers import build_driver_frame, PERIODS
from src.income_statement import build_income_statement
from src.working_capital import build_working_capital
from src.debt_schedule import build_debt_schedule
from src.equity_schedule import build_equity_schedule
from src.balance_sheet import build_balance_sheet, check_balance_sheet_balances
from src.cash_flow import build_cash_flow_statement, check_cash_flow_ties_to_debt_schedule
from src.opening_balances import compute_retained_earnings_plug

TOLERANCE = 0.01
MAX_ITERATIONS = 50


def run_three_statement_model(periods=PERIODS):
    """
    Run the full three statement model pipeline.
    Iterates on interest expense until it converges, as defined
    by tolerance.
    Return a dict of every DataFrame built by pipeline modules.
    """
    drivers = build_driver_frame(periods=periods)
    interest_expense = {period: 0.0 for period in periods}

    for iteration in range(1, MAX_ITERATIONS + 1):
        income_statement = build_income_statement(
            drivers, periods=periods, interest_expense=interest_expense
        )
        working_capital = build_working_capital(drivers, income_statement)
        debt_schedule = build_debt_schedule(
            drivers, income_statement, working_capital, periods=periods
        )

        calc_interest_expense = debt_schedule.loc["Total Interest Expense"].to_dict()
        max_period_diff = max(
            abs(calc_interest_expense[period] - interest_expense[period])
            for period in periods
        )
        interest_expense = calc_interest_expense

        if max_period_diff < TOLERANCE:
            print(f"Interest expense converged after {iteration} iterations")
            break
    else:
        print(f"Warning: Interest expense did not converge within max iterations.")
        print(f"Max Change is still above tolerance at: {max_period_diff: .2f}")

    #Final pass with fully converged interst expense
    #All statements and schdules run
    income_statement = build_income_statement(
        drivers, periods=periods, interest_expense=interest_expense
    )
    working_capital = build_working_capital(drivers, income_statement, periods=periods)
    debt_schedule = build_debt_schedule(
        drivers, income_statement, working_capital, periods=periods
    )
    retained_earnings_plug = compute_retained_earnings_plug(
        working_capital, debt_schedule, periods
    )
    equity_schedule = build_equity_schedule(
        drivers, income_statement,
        beginning_retained_earnings=retained_earnings_plug,
        periods=periods
    )
    balance_sheet = build_balance_sheet(
        drivers, income_statement, working_capital,
        debt_schedule, equity_schedule,
        periods=periods
    )
    cash_flow_statement = build_cash_flow_statement(
        drivers, income_statement, working_capital,
        debt_schedule, equity_schedule,
        periods=periods
    )

    return {
        "drivers": drivers,
        "income_statement": income_statement,
        "working_capital": working_capital,
        "debt_schedule": debt_schedule,
        "equity_schedule": equity_schedule,
        "balance_sheet": balance_sheet,
        "cash_flow_statement": cash_flow_statement,
    }
    

#Test Main
if __name__ == "__main__":
    #Run the fully converged model
    #Verify both becks still pass
    results = run_three_statement_model()
    check_balance_sheet_balances(results["balance_sheet"])
    check_cash_flow_ties_to_debt_schedule(results["cash_flow_statement"])


