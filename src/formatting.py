#Terminal output formatting module for three statement model
"""
Renders a statement DataFrame as a bordered, formatted table
in the terminal using tabulate instead of panda's detault printout.

Numbers are formatted with thousands separators and no deciaml
places. A title separates each statement visually.

Presentation only. Does not modify any underlying DataFrame.
"""
import pandas as pd
from tabulate import tabulate


def format_currency(value):
    """
    Format a number as a dollar amount with thousands separators.
    Negative values use standard finance convention (parenths)
    """
    if not pd.notna(value):
        return ""
    if value < 0:
        return f"${abs(value):,.0f}"
    return f"${value:,.0f}"


def print_statement(df, title):
    """
    Print a statement DataFrame as a formatted terminal table.
    (line items as rows, periods as columns)

    df: DataFrame from any build module
    title: string heading printed above the table
    """
    formatted = df.copy()
    for column in formatted.columns:
        formatted[column] = formatted[column].apply(format_currency)
    
    print(f"\n{'='*60}")
    print(f"   {title}")
    print(f"\n{'='*60}")
    print(tabulate(formatted, headers="keys", tablefmt="fancy_outline"))
    print()


def pd_notna(value):
    """
    Small local wrapper so this module doesn't need a full pandas import
    """
    return value == value and value is not None