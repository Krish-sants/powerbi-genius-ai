"""DAX Measure generator — produces standard and advanced DAX expressions for Power BI."""
from typing import Dict, List
from models.schemas import DAXMeasure


DAX_LIBRARY: Dict[str, str] = {
    "Total Revenue": "Total Revenue = SUM('{table}'[{col}])",
    "Total Orders": "Total Orders = COUNTROWS('{table}')",
    "Avg Order Value": "Avg Order Value = AVERAGEX('{table}', '{table}'[{col}])",
    "Profit Margin %": "Profit Margin % = DIVIDE([Total Profit], [Total Revenue], 0) * 100",
    "YoY Growth %": """YoY Growth % =
VAR CurrentYear = [Total Revenue]
VAR PriorYear = CALCULATE([Total Revenue], SAMEPERIODLASTYEAR('Date'[Date]))
RETURN DIVIDE(CurrentYear - PriorYear, PriorYear, 0) * 100""",
    "MoM Growth %": """MoM Growth % =
VAR CurrentMonth = [Total Revenue]
VAR PriorMonth = CALCULATE([Total Revenue], DATEADD('Date'[Date], -1, MONTH))
RETURN DIVIDE(CurrentMonth - PriorMonth, PriorMonth, 0) * 100""",
    "Revenue Running Total": """Revenue Running Total =
CALCULATE([Total Revenue],
  FILTER(ALL('Date'), 'Date'[Date] <= MAX('Date'[Date])))""",
    "Rolling 3M Revenue": """Rolling 3M Revenue =
CALCULATE([Total Revenue],
  DATESINPERIOD('Date'[Date], LASTDATE('Date'[Date]), -3, MONTH))""",
    "Rolling 12M Revenue": """Rolling 12M Revenue =
CALCULATE([Total Revenue],
  DATESINPERIOD('Date'[Date], LASTDATE('Date'[Date]), -12, MONTH))""",
    "Unique Customers": "Unique Customers = DISTINCTCOUNT('{table}'[{col}])",
    "Customer LTV": "Customer LTV = DIVIDE([Total Revenue], [Unique Customers], 0)",
    "Revenue Rank": "Revenue Rank = RANKX(ALL('{table}'[{col}]), [Total Revenue], , DESC, Dense)",
    "Gross Margin %": "Gross Margin % = DIVIDE([Gross Margin], [Total Revenue], 0) * 100",
    "ROI": "ROI = DIVIDE([Net Profit], [Total Investment], 0) * 100",
    "Attrition Rate": """Attrition Rate =
DIVIDE(
    CALCULATE(COUNTROWS(Employees), Employees[Status] = "Terminated"),
    COUNTROWS(Employees), 0
) * 100""",
    "Headcount": "Headcount = CALCULATE(COUNTROWS(Employees), Employees[Status] = \"Active\")",
    "Dynamic Measure": """Dynamic Measure =
SWITCH(
    SELECTEDVALUE(MeasureSelector[Measure]),
    "Revenue", [Total Revenue],
    "Profit", [Total Profit],
    "Customers", [Unique Customers],
    [Total Revenue]
)""",
}


def generate_measures_for_dataset(
    fact_table: str, metric_cols: List[str], id_col: str = None, date_col: str = None
) -> List[DAXMeasure]:
    measures: List[DAXMeasure] = []

    for col in metric_cols[:5]:
        measures.append(DAXMeasure(
            name=f"Total {col.replace('_', ' ').title()}",
            expression=f"Total {col.replace('_', ' ').title()} = SUM('{fact_table}'[{col}])",
            table=fact_table,
            format_string="#,##0.00",
            description=f"Sum of {col}",
        ))
        measures.append(DAXMeasure(
            name=f"Avg {col.replace('_', ' ').title()}",
            expression=f"Avg {col.replace('_', ' ').title()} = AVERAGE('{fact_table}'[{col}])",
            table=fact_table,
            format_string="#,##0.00",
            description=f"Average of {col}",
        ))

    if id_col:
        measures.append(DAXMeasure(
            name=f"Unique {id_col.replace('_', ' ').title()}",
            expression=f"Unique {id_col.replace('_', ' ').title()} = DISTINCTCOUNT('{fact_table}'[{id_col}])",
            table=fact_table,
            format_string="#,##0",
            description=f"Count of distinct {id_col}",
        ))

    if date_col and metric_cols:
        measures.append(DAXMeasure(
            name="YoY Growth %",
            expression=DAX_LIBRARY["YoY Growth %"],
            table=fact_table,
            format_string="+0.0%;-0.0%;0.0%",
            description="Year-over-year growth percentage",
        ))
        measures.append(DAXMeasure(
            name="Rolling 3M",
            expression=DAX_LIBRARY["Rolling 3M Revenue"],
            table=fact_table,
            format_string="#,##0.00",
            description="3-month rolling average",
        ))

    return measures


def generate_full_dax_script(measures: List[DAXMeasure]) -> str:
    lines = ["// Auto-generated DAX Measures — PowerBI Genius AI\n"]
    for m in measures:
        lines.append(f"// {m.description}")
        lines.append(m.expression)
        lines.append("")
    return "\n".join(lines)
