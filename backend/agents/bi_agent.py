"""Agent 4: Business Intelligence Agent — auto-generates KPIs, metrics, DAX measures."""
import json
import numpy as np
import pandas as pd
from typing import Any, Dict, List
from loguru import logger

from models.schemas import KPIDefinition, BusinessDomain
from services.llm_service import chat_json


class BIAgent:
    name = "bi_agent"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[BIAgent] Starting for job {state['job_id']}")
        try:
            df = pd.DataFrame(state["cleaned_data"]["data"])
            domain = BusinessDomain(state.get("domain", "unknown"))
            data_dict = state.get("data_dictionary", {})
            entity_mapping = state.get("entity_mapping", {})

            kpis = await self._generate_kpis(df, domain, data_dict, entity_mapping)
            state["kpis"] = [k.dict() for k in kpis]

            data_model = await self._generate_data_model(df, domain, data_dict)
            state["data_model"] = data_model

            state["agent_statuses"]["bi_agent"] = "completed"
            state["progress"] = 60
            logger.info(f"[BIAgent] Generated {len(kpis)} KPIs")
        except Exception as e:
            logger.error(f"[BIAgent] Error: {e}")
            state["agent_statuses"]["bi_agent"] = "failed"
            state["errors"].append(f"BI error: {str(e)}")
        return state

    async def _generate_kpis(
        self, df: pd.DataFrame, domain: BusinessDomain,
        data_dict: Dict, entity_mapping: Dict
    ) -> List[KPIDefinition]:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

        prompt = f"""You are a Power BI expert. Given this dataset, identify and compute the most important KPIs.

Domain: {domain.value}
All columns: {list(df.columns)}
Numeric columns: {numeric_cols}
Date columns: {date_cols}
Data dictionary: {json.dumps(data_dict, default=str)}
Entity mapping: {json.dumps(entity_mapping, default=str)}

Return JSON with KPI definitions. Only use columns that actually exist in the dataset. Limit to 8 KPIs.
{{
  "kpis": [
    {{
      "name": "total_revenue",
      "display_name": "Total Revenue",
      "category": "Revenue",
      "formula": "SUM(revenue)",
      "dax_measure": "Total Revenue = SUM('Data'[revenue])",
      "source_column": "revenue",
      "aggregation": "sum",
      "unit": "$",
      "description": "Total revenue generated",
      "priority": 1
    }}
  ]
}}"""

        result = await chat_json([{"role": "user", "content": prompt}])
        kpi_list = result.get("kpis", [])

        results: List[KPIDefinition] = []
        for kpi_def in kpi_list:
            col = kpi_def.get("source_column")
            value = None
            if col and col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                agg = kpi_def.get("aggregation", "sum")
                if agg == "sum":       value = float(df[col].sum())
                elif agg == "avg":     value = float(df[col].mean())
                elif agg == "count":   value = float(df[col].count())
                elif agg == "distinct_count": value = float(df[col].nunique())
                elif agg == "percentage":     value = float(df[col].mean() * 100)

            results.append(KPIDefinition(
                name=kpi_def.get("name", "kpi"),
                display_name=kpi_def.get("display_name", kpi_def.get("name", "")),
                category=kpi_def.get("category", "General"),
                formula=kpi_def.get("formula", ""),
                dax_measure=kpi_def.get("dax_measure", ""),
                value=value,
                formatted_value=self._format_value(value, kpi_def.get("unit", "")) if value is not None else "N/A",
                unit=kpi_def.get("unit", ""),
                description=kpi_def.get("description", ""),
                priority=kpi_def.get("priority", 1),
            ))

        results.append(KPIDefinition(
            name="total_records", display_name="Total Records",
            category="Data Volume", formula="COUNT(*)",
            dax_measure="Total Records = COUNTROWS('Data')",
            value=float(len(df)), formatted_value=f"{len(df):,}",
            unit="", description="Total number of data records", priority=5,
        ))
        return sorted(results, key=lambda k: k.priority)

    def _format_value(self, value: float, unit: str) -> str:
        if unit == "$":
            if abs(value) >= 1_000_000_000: return f"${value/1_000_000_000:.2f}B"
            elif abs(value) >= 1_000_000:   return f"${value/1_000_000:.2f}M"
            elif abs(value) >= 1_000:        return f"${value/1_000:.1f}K"
            return f"${value:,.2f}"
        elif unit == "%": return f"{value:.1f}%"
        elif abs(value) >= 1_000_000: return f"{value/1_000_000:.2f}M"
        elif abs(value) >= 1_000:     return f"{value/1_000:.1f}K"
        return f"{value:,.2f}"

    async def _generate_data_model(
        self, df: pd.DataFrame, domain: BusinessDomain, data_dict: Dict
    ) -> Dict[str, Any]:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = [c for c in df.columns if df[c].dtype == object and df[c].nunique() < 50]
        date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()

        prompt = f"""You are a Power BI data architect. Design a star schema data model for this dataset.

Domain: {domain.value}
All columns: {list(df.columns)}
Numeric columns (metrics): {numeric_cols}
Categorical columns (dimensions): {categorical_cols}
Date columns: {date_cols}

Return JSON with the data model and DAX measures:
{{
  "fact_tables": ["FactSales"],
  "dimension_tables": ["DimDate", "DimProduct", "DimCustomer"],
  "relationships": [
    {{"from": "FactSales[ProductKey]", "to": "DimProduct[ProductKey]", "cardinality": "many-to-one"}}
  ],
  "dax_measures": [
    {{
      "name": "Total Revenue",
      "expression": "Total Revenue = SUM(FactSales[revenue])",
      "table": "FactSales",
      "format_string": "$#,##0.00",
      "description": "Total revenue"
    }}
  ],
  "calculated_columns": []
}}"""

        return await chat_json([{"role": "user", "content": prompt}])
