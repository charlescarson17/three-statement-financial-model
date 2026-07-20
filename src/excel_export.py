#Excel export module for the three statement model
"""
Exports the full model to a sinlge formatted .xlsx workbook
using xlsxwriter. One tab per section in the pipeline order.

Formatting:
    Bold header row and bold first column
    Frozen panes so labels stay visible
    Conditional formatting on check rows

Two tabs use non-standard layouts and are handled separately:
    Drivers
    Opening balances

This is presentation only. It does not moditfy or recompute.
"""

import xlsxwriter

STATEMENT_SHEETS = [
    ("Income Statement", "income_statement"),
    ("Working Capital", "working_capital"),
    ("Debt Schedule", "debt_schedule"),
    ("Equity Schedule", "equity_schedule"),
    ("Balance Sheet", "balance_sheet"),
    ("Cash Flow Statement", "cash_flow_statement"),
]

CHECK_ROWS = {"Balance Check", "Cash Tie-Out Check"}

TOTAL_LINE_ITEMS = {
    "Net Income",
    "Total Assets",
    "Total Liabilities & Equity",
    "Net Change in Cash",
    "Ending Cash",
}

SUBTOTAL_LINE_ITEMS = {
    "Gross Profit",
    "EBITDA",
    "EBIT",
    "Pretax Income",
    "Cash Flow from Operations",
    "Cash Flow from Investing",
    "Cash Flow from Financing",
    "Total Liabilities",
    "Total Equity",
}

SUBSUBTOTAL_LINE_ITEMS = {
    "Total Current Assets",
    "Total Current Liabilities",
}

INDENTED_ITEMS_BY_SHEET = {
    "Balance Sheet": {
        "Cash", "Accounts Receivable", "Inventory", "Other Current Assets",
        "Accounts Payable", "Accrued Liabilities", "Revolver",
    },
}


def _build_formats(workbook):
    return {
        "header": workbook.add_format({
            "bold": True, "bg_color": "#1F4E78", "font_color": "white",
            "align": "center", "border": 1,
        }),
        "label": workbook.add_format({
            "bold": True, "bg_color": "#D9E1F2", "border": 1,
        }),
        "label_indent": workbook.add_format({
            "bold": True, "bg_color": "#D9E1F2", "border": 1, "indent": 1,
        }),
        "currency": workbook.add_format({
            "num_format": "$#,##0;($#,##0)", "border": 1,
        }),
        "decimal": workbook.add_format({
            "num_format": "#,##0.0000", "border": 1,
        }),
        "subsubtotal": workbook.add_format({
            "num_format": "$#,##0;($#,##0)", "border": 1,
            "bold": True, "top": 1, "top_color": "#A6A6A6",
        }),
        "subtotal": workbook.add_format({
            "num_format": "$#,##0;($#,##0)", "border": 1,
            "bold": True, "top": 1,
        }),
        "total": workbook.add_format({
            "num_format": "$#,##0;($#,##0)", "border": 1,
            "bold": True, "top": 1, "bottom": 6,
        }),
        "pass": workbook.add_format({
            "bg_color": "#C6EFCE", "font_color": "#006100",
            "num_format": "$#,##0;($#,##0)", "border": 1,
        }),
        "fail": workbook.add_format({
            "bg_color": "#FFC7CE", "font_color": "#9C0006",
            "num_format": "$#,##0;($#,##0)", "border": 1,
        }),
    }


def _write_statement_sheet(workbook, sheet_title, df, formats, value_format_key="currency"):
    """Write a period-column DataFrame (line items as rows, periods as
    columns) to its own worksheet."""
    worksheet = workbook.add_worksheet(sheet_title)
    indented_items = INDENTED_ITEMS_BY_SHEET.get(sheet_title, set())

    worksheet.write(0, 0, "", formats["header"])
    for col_idx, period in enumerate(df.columns, start=1):
        worksheet.write(0, col_idx, period, formats["header"])

    longest_label = 0
    for row_idx, line_item in enumerate(df.index, start=1):
        label_fmt = formats["label_indent"] if line_item in indented_items else formats["label"]
        worksheet.write(row_idx, 0, line_item, label_fmt)
        longest_label = max(longest_label, len(line_item))

        for col_idx, period in enumerate(df.columns, start=1):
            value = df.loc[line_item, period]

            if line_item in CHECK_ROWS:
                fmt = formats["pass"] if abs(value) < 0.01 else formats["fail"]
            elif line_item in TOTAL_LINE_ITEMS:
                fmt = formats["total"]
            elif line_item in SUBTOTAL_LINE_ITEMS:
                fmt = formats["subtotal"]
            elif line_item in SUBSUBTOTAL_LINE_ITEMS:
                fmt = formats["subsubtotal"]
            else:
                fmt = formats[value_format_key]

            worksheet.write_number(row_idx, col_idx, value, fmt)

    worksheet.set_column(0, 0, longest_label + 4)
    worksheet.set_column(1, len(df.columns), 16)
    worksheet.freeze_panes(1, 1)


def _write_opening_balances_sheet(workbook, opening_balances, retained_earnings_plug, formats):
    """Write the flat opening balances dict (plus the computed retained
    earnings plug) as a simple two-column Assumption/Value table."""
    worksheet = workbook.add_worksheet("Opening Balances")

    worksheet.write(0, 0, "Assumption", formats["header"])
    worksheet.write(0, 1, "Value", formats["header"])

    row_idx = 1
    for name, value in opening_balances.items():
        worksheet.write(row_idx, 0, name, formats["label"])
        worksheet.write_number(row_idx, 1, value, formats["currency"])
        row_idx += 1

    worksheet.write(row_idx, 0, "retained_earnings (computed plug)", formats["label"])
    worksheet.write_number(row_idx, 1, retained_earnings_plug, formats["total"])

    worksheet.set_column(0, 0, 34)
    worksheet.set_column(1, 1, 16)
    worksheet.freeze_panes(1, 0)


def export_to_excel(results, filepath="outputs/model_output.xlsx"):
    """
    Export the full model in `results` to a formatted multi-tab Excel
    workbook: Drivers, Opening Balances, then each statement/schedule
    in pipeline order.
    """
    workbook = xlsxwriter.Workbook(filepath)
    formats = _build_formats(workbook)

    _write_statement_sheet(
        workbook, "Drivers", results["drivers"], formats, value_format_key="decimal"
    )
    _write_opening_balances_sheet(
        workbook, results["opening_balances"], results["retained_earnings_plug"], formats
    )

    for sheet_title, results_key in STATEMENT_SHEETS:
        _write_statement_sheet(workbook, sheet_title, results[results_key], formats)

    workbook.close()
    print(f"Excel workbook written to {filepath}")


