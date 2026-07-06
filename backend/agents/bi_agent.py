"""Agent 4: Business Intelligence Agent — auto-generates KPIs, metrics, DAX measures."""
import asyncio
import json
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger

from models.schemas import KPIDefinition, BusinessDomain
from services.llm_service import chat_json
from utils import df_cache


class BIAgent:
    name = "bi_agent"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[BIAgent] Starting for job {state['job_id']}")
        try:
            df = df_cache.get_or_rebuild(state["job_id"], "cleaned", state.get("cleaned_data"))
            domain = BusinessDomain(state.get("domain", "unknown"))
            data_dict = state.get("data_dictionary", {})
            entity_mapping = state.get("entity_mapping", {})
            quality_report = state.get("quality_report", {})

            # The two LLM calls are independent — run them concurrently
            kpis, data_model = await asyncio.gather(
                self._generate_kpis(df, domain, data_dict, entity_mapping, quality_report),
                self._generate_data_model(df, domain, data_dict),
            )
            state["kpis"] = [k.dict() for k in kpis]
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
        data_dict: Dict, entity_mapping: Dict, quality_report: Dict
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

Return JSON with KPI definitions. Only use columns that actually exist in the dataset. Limit to 12 KPIs.
Cover multiple categories (Revenue, Growth, Volume, Efficiency, Customer, Profitability) where the columns support them.
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
}}
Valid aggregations: sum, avg, median, min, max, count, distinct_count, percentage."""

        result = await chat_json([{"role": "user", "content": prompt}])
        kpi_list = result.get("kpis", [])
        date_col = date_cols[0] if date_cols else None

        results: List[KPIDefinition] = []
        for kpi_def in kpi_list[:12]:
            col = kpi_def.get("source_column")
            agg = kpi_def.get("aggregation", "sum")
            # A %-unit average is a ratio KPI — route through the guarded percentage logic
            if kpi_def.get("unit") == "%" and agg == "avg":
                agg = "percentage"
            value = self._compute_value(df, col, agg)

            trend, trend_pct = (None, None)
            if value is not None and date_col and agg in ("sum", "avg", "count"):
                trend, trend_pct = self._compute_trend(df, col, date_col, agg)

            results.append(KPIDefinition(
                name=kpi_def.get("name", "kpi"),
                display_name=kpi_def.get("display_name", kpi_def.get("name", "")),
                category=kpi_def.get("category", "General"),
                formula=kpi_def.get("formula", ""),
                dax_measure=kpi_def.get("dax_measure", ""),
                value=value,
                formatted_value=self._format_value(value, kpi_def.get("unit", "")) if value is not None else "N/A",
                trend=trend,
                trend_percentage=trend_pct,
                unit=kpi_def.get("unit", ""),
                description=kpi_def.get("description", ""),
                priority=kpi_def.get("priority", 1),
            ))

        results.extend(self._compute_auto_kpis(df, numeric_cols, date_cols, quality_report))

        # De-duplicate by name (LLM KPIs win), then rank
        seen: Dict[str, KPIDefinition] = {}
        for k in results:
            if k.name not in seen:
                seen[k.name] = k
        return sorted(seen.values(), key=lambda k: k.priority)

    def _compute_value(self, df: pd.DataFrame, col: Optional[str], agg: str) -> Optional[float]:
        if not col or col not in df.columns:
            return None
        series = df[col]
        if agg in ("count", "distinct_count"):
            return float(series.count()) if agg == "count" else float(series.nunique())
        if not pd.api.types.is_numeric_dtype(series):
            return None
        if agg == "sum":        return float(series.sum())
        elif agg == "avg":      return float(series.mean())
        elif agg == "median":   return float(series.median())
        elif agg == "min":      return float(series.min())
        elif agg == "max":      return float(series.max())
        elif agg == "percentage":
            # Only meaningful for ratio-like columns; a raw metric (e.g. revenue)
            # would produce a nonsense number, so return N/A instead.
            max_abs = float(series.abs().max())
            if max_abs <= 1.5:  return float(series.mean() * 100)   # 0–1 fractions
            if max_abs <= 100:  return float(series.mean())          # already 0–100
            return None
        return None

    def _compute_trend(
        self, df: pd.DataFrame, col: str, date_col: str, agg: str
    ) -> Tuple[Optional[str], Optional[float]]:
        """Period-over-period movement: compare the last full period against the previous one."""
        try:
            ts = df[[date_col, col]].dropna()
            if len(ts) < 4 or not pd.api.types.is_numeric_dtype(ts[col]):
                return None, None
            span_days = (ts[date_col].max() - ts[date_col].min()).days
            freq = "D" if span_days <= 31 else "W" if span_days <= 120 else "M" if span_days <= 1100 else "Y"
            agg_fn = "mean" if agg == "avg" else "count" if agg == "count" else "sum"
            grouped = ts.groupby(ts[date_col].dt.to_period(freq))[col].agg(agg_fn)
            if len(grouped) < 2:
                return None, None
            prev, last = float(grouped.iloc[-2]), float(grouped.iloc[-1])
            if prev == 0:
                return None, None
            pct = (last - prev) / abs(prev) * 100
            trend = "up" if pct > 1 else "down" if pct < -1 else "stable"
            return trend, round(pct, 2)
        except Exception as e:
            logger.warning(f"[BIAgent] Trend computation failed for {col}: {e}")
            return None, None

    @staticmethod
    def _pick_primary_metric(df: pd.DataFrame, numeric_cols: List[str]) -> Optional[str]:
        """Prefer business-metric columns; skip identifier-like numeric columns."""
        preferred = ("revenue", "sales", "amount", "profit", "total", "value", "price", "cost", "qty", "quantity")
        for name in preferred:
            for col in numeric_cols:
                if name in col.lower():
                    return col
        for col in numeric_cols:
            lower = col.lower()
            looks_like_id = lower.endswith(("id", "key", "code", "number", "no")) or lower.startswith("id")
            all_unique_int = pd.api.types.is_integer_dtype(df[col]) and df[col].nunique() >= len(df) * 0.95
            if not looks_like_id and not all_unique_int:
                return col
        return None

    def _compute_auto_kpis(
        self, df: pd.DataFrame, numeric_cols: List[str],
        date_cols: List[str], quality_report: Dict
    ) -> List[KPIDefinition]:
        """KPIs computed directly from the data — no LLM required, always present."""
        kpis: List[KPIDefinition] = [KPIDefinition(
            name="total_records", display_name="Total Records",
            category="Data Volume", formula="COUNT(*)",
            dax_measure="Total Records = COUNTROWS('Data')",
            value=float(len(df)), formatted_value=f"{len(df):,}",
            unit="", description="Total number of data records", priority=5,
        )]

        quality_score = quality_report.get("overall_score")
        if quality_score is not None:
            kpis.append(KPIDefinition(
                name="data_quality_score", display_name="Data Quality Score",
                category="Quality", formula="Composite quality score",
                dax_measure="", value=float(quality_score),
                formatted_value=f"{quality_score:.0f}/100", unit="",
                description="Composite score: completeness, duplicates, outliers, format consistency",
                priority=6,
            ))

        # Primary metric extras: period growth, average per record
        metric = self._pick_primary_metric(df, numeric_cols)
        if metric:
            avg_val = float(df[metric].mean())
            kpis.append(KPIDefinition(
                name=f"avg_{metric}", display_name=f"Avg {metric.replace('_', ' ').title()}",
                category="Efficiency", formula=f"AVG({metric})",
                dax_measure=f"Avg {metric} = AVERAGE('Data'[{metric}])",
                value=avg_val, formatted_value=self._format_value(avg_val, ""),
                unit="", description=f"Average {metric} per record", priority=4,
            ))
            if date_cols:
                trend, pct = self._compute_trend(df, metric, date_cols[0], "sum")
                if pct is not None:
                    kpis.append(KPIDefinition(
                        name=f"{metric}_growth", display_name=f"{metric.replace('_', ' ').title()} Growth",
                        category="Growth", formula="Last period vs previous period",
                        dax_measure=(
                            f"{metric} Growth % = DIVIDE([Current Period {metric}] - "
                            f"[Previous Period {metric}], [Previous Period {metric}])"
                        ),
                        value=pct, formatted_value=f"{pct:+.1f}%",
                        trend=trend, trend_percentage=pct, unit="%",
                        description=f"Period-over-period change in total {metric}", priority=2,
                    ))

        # Concentration: how much of the primary metric the top category holds.
        # Use the lowest-cardinality dimension (e.g. region) for concentration and
        # the highest-cardinality one (e.g. customer) for the distinct count.
        cat_cols = sorted(
            (c for c in df.columns if df[c].dtype == object and 1 < df[c].nunique() < 50),
            key=lambda c: df[c].nunique(),
        )
        if metric and cat_cols:
            cat = cat_cols[0]
            by_cat = df.groupby(cat)[metric].sum()
            total = float(by_cat.sum())
            if total:
                top_share = float(by_cat.max()) / total * 100
                kpis.append(KPIDefinition(
                    name=f"top_{cat}_share", display_name=f"Top {cat.replace('_', ' ').title()} Share",
                    category="Concentration", formula=f"MAX(SUM({metric}) by {cat}) / SUM({metric})",
                    dax_measure=f"Top {cat} Share = DIVIDE(MAXX(VALUES('Data'[{cat}]), CALCULATE(SUM('Data'[{metric}]))), SUM('Data'[{metric}]))",
                    value=top_share, formatted_value=f"{top_share:.1f}%", unit="%",
                    description=f"Share of total {metric} held by the largest {cat} ('{by_cat.idxmax()}')",
                    priority=3,
                ))
            entity = cat_cols[-1]
            kpis.append(KPIDefinition(
                name=f"unique_{entity}", display_name=f"Unique {entity.replace('_', ' ').title()}s",
                category="Data Volume", formula=f"DISTINCTCOUNT({entity})",
                dax_measure=f"Unique {entity} = DISTINCTCOUNT('Data'[{entity}])",
                value=float(df[entity].nunique()), formatted_value=f"{df[entity].nunique():,}",
                unit="", description=f"Number of distinct {entity} values", priority=4,
            ))

        # Date coverage
        if date_cols:
            dc = date_cols[0]
            dmin, dmax = df[dc].min(), df[dc].max()
            if pd.notna(dmin) and pd.notna(dmax):
                days = max((dmax - dmin).days, 1)
                kpis.append(KPIDefinition(
                    name="date_coverage", display_name="Date Coverage",
                    category="Time", formula=f"MAX({dc}) - MIN({dc})",
                    dax_measure=f"Date Coverage = DATEDIFF(MIN('Data'[{dc}]), MAX('Data'[{dc}]), DAY)",
                    value=float(days),
                    formatted_value=f"{days / 365.25:.1f} yrs" if days >= 365 else f"{days} days",
                    unit="", description=f"Time span covered: {dmin:%Y-%m-%d} to {dmax:%Y-%m-%d}",
                    priority=5,
                ))
        return kpis

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
