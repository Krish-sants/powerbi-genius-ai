"""Agent 6: Dashboard Design Agent — generates full Power BI dashboard spec with pages, charts, slicers."""
import json
import uuid
import numpy as np
import pandas as pd
from typing import Any, Dict, List
from loguru import logger

from models.schemas import (
    DashboardSpec, DashboardPage, ChartSpec,
    BusinessDomain, KPIDefinition, Insight
)
from services.llm_service import chat_json
from utils import df_cache

COLOR_PALETTES = {
    "executive_dark": ["#1A1F36", "#6366F1", "#22D3EE", "#10B981", "#F59E0B", "#EF4444", "#A855F7", "#EC4899"],
}

EXECUTIVE_THEME = {
    "background": "#0F172A", "surface": "#1E293B", "card": "#1E293B",
    "accent": "#6366F1", "accent2": "#22D3EE", "text": "#F8FAFC",
    "text_muted": "#94A3B8", "success": "#10B981", "warning": "#F59E0B",
    "danger": "#EF4444", "border": "#334155",
}


class DashboardAgent:
    name = "dashboard_agent"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[DashboardAgent] Starting for job {state['job_id']}")
        try:
            df = df_cache.get_or_rebuild(state["job_id"], "cleaned", state.get("cleaned_data"))
            domain = BusinessDomain(state.get("domain", "unknown"))
            kpis = [KPIDefinition(**k) for k in state.get("kpis", [])]
            insights = [Insight(**i) for i in state.get("insights", [])]
            data_dict = state.get("data_dictionary", {})
            business_context = state.get("business_context", "")

            spec = await self._design_dashboard(df, domain, kpis, insights, data_dict, business_context)
            state["dashboard_spec"] = spec.dict()
            state["theme"] = EXECUTIVE_THEME

            state["agent_statuses"]["dashboard_agent"] = "completed"
            state["progress"] = 90
            logger.info(f"[DashboardAgent] Dashboard spec created: {len(spec.pages)} pages")
        except Exception as e:
            logger.error(f"[DashboardAgent] Error: {e}")
            state["agent_statuses"]["dashboard_agent"] = "failed"
            state["errors"].append(f"Dashboard error: {str(e)}")
        return state

    async def _design_dashboard(
        self, df: pd.DataFrame, domain: BusinessDomain,
        kpis: List[KPIDefinition], insights: List[Insight],
        data_dict: Dict, business_context: str
    ) -> DashboardSpec:
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = [c for c in df.columns if df[c].dtype == object and df[c].nunique() < 50]
        date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
        all_cols = list(df.columns)
        kpi_names = [k.display_name for k in kpis[:6]]

        # Keep each page spec concise — max 3 charts per page to avoid truncation
        prompt = f"""Design a 6-page Power BI dashboard for a {domain.value} business dataset.
IMPORTANT: Return ONLY valid JSON. No markdown, no comments, no trailing commas.

Available columns: {all_cols}
Numeric: {numeric_cols[:8]}
Categorical: {categorical_cols[:6]}
Date: {date_cols[:2]}
KPIs: {kpi_names}

Pages to design (3 charts max each):
1. Executive Overview — kpi_card tiles + one summary bar
2. Trend Analysis — line/area chart over time
3. Category Breakdown — bar/pie by categorical columns
4. Performance Analysis — scatter or ranked bar
5. Detailed Data — table + distribution
6. AI Insights — narrative cards

Return this exact JSON structure:
{{"title": "string", "subtitle": "string", "pages": [{{"page_number": 1, "title": "string", "description": "string", "charts": [{{"chart_id": "c1", "chart_type": "bar", "title": "string", "x_axis": "col_name_or_null", "y_axis": "col_name_or_null", "color_by": null, "data_columns": ["col"], "position": {{"x": 0, "y": 0, "width": 6, "height": 4}}, "config": {{}}}}], "slicers": []}}], "slicers": [], "bookmarks": []}}

Rules:
- Use ONLY column names from: {all_cols}
- chart_type must be one of: kpi_card, bar, line, area, pie, donut, scatter, table
- x_axis and y_axis must be column names or null
- No trailing commas anywhere"""

        try:
            spec_data = await chat_json([{"role": "user", "content": prompt}], max_tokens=6000)
        except Exception as e:
            logger.warning(f"[DashboardAgent] LLM spec failed ({e}), using fallback generator")
            spec_data = self._fallback_spec(domain, numeric_cols, categorical_cols, date_cols, kpis)
            return self._build_spec(spec_data, domain, kpis, insights)

        return self._build_spec(spec_data, domain, kpis, insights)

    def _build_spec(self, spec_data: Dict, domain: BusinessDomain,
                    kpis: List[KPIDefinition], insights: List[Insight]) -> DashboardSpec:
        pages = []
        for page_data in spec_data.get("pages", []):
            charts = [
                ChartSpec(
                    chart_id=c.get("chart_id", str(uuid.uuid4())),
                    chart_type=c.get("chart_type", "bar"),
                    title=c.get("title", ""),
                    subtitle=c.get("subtitle"),
                    x_axis=c.get("x_axis"),
                    y_axis=c.get("y_axis"),
                    color_by=c.get("color_by"),
                    data_columns=c.get("data_columns", []),
                    page=page_data.get("page_number", 1),
                    position=c.get("position", {"x": 0, "y": 0, "width": 6, "height": 4}),
                    config=c.get("config", {}),
                )
                for c in page_data.get("charts", [])
            ]
            pages.append(DashboardPage(
                page_number=page_data.get("page_number", len(pages) + 1),
                title=page_data.get("title", f"Page {len(pages) + 1}"),
                description=page_data.get("description", ""),
                charts=charts,
                slicers=page_data.get("slicers", []),
            ))

        return DashboardSpec(
            dashboard_id=str(uuid.uuid4()),
            title=spec_data.get("title", f"{domain.value.title()} Intelligence Dashboard"),
            subtitle=spec_data.get("subtitle", "AI-Generated Executive Dashboard"),
            domain=domain,
            theme="executive_dark",
            pages=pages,
            kpis=kpis,
            insights=insights,
            slicers=spec_data.get("slicers", []),
            bookmarks=spec_data.get("bookmarks", []),
            color_palette=COLOR_PALETTES["executive_dark"],
            font_family="Segoe UI",
        )

    def _fallback_spec(self, domain: BusinessDomain, numeric_cols: List, categorical_cols: List,
                       date_cols: List, kpis: List[KPIDefinition]) -> Dict:
        """Generate a basic dashboard spec from column metadata without LLM."""
        num = numeric_cols[:4]
        cat = categorical_cols[:2]
        date = date_cols[0] if date_cols else None
        main_metric = num[0] if num else None
        second_metric = num[1] if len(num) > 1 else main_metric

        pages = [
            {"page_number": 1, "title": "Executive Overview", "description": "Key metrics at a glance",
             "charts": [
                 {"chart_id": f"c{i+1}", "chart_type": "kpi_card", "title": k.display_name,
                  "x_axis": None, "y_axis": main_metric, "color_by": None,
                  "data_columns": [main_metric] if main_metric else [],
                  "position": {"x": i * 3, "y": 0, "width": 3, "height": 2}, "config": {}}
                 for i, k in enumerate(kpis[:4])
             ], "slicers": [date] if date else []},
            {"page_number": 2, "title": "Trend Analysis", "description": "Performance over time",
             "charts": [
                 {"chart_id": "c5", "chart_type": "line", "title": f"{main_metric} Over Time",
                  "x_axis": date, "y_axis": main_metric, "color_by": None,
                  "data_columns": [c for c in [date, main_metric] if c],
                  "position": {"x": 0, "y": 0, "width": 12, "height": 4}, "config": {}}
             ] if date and main_metric else [], "slicers": []},
            {"page_number": 3, "title": "Category Breakdown", "description": "Performance by segment",
             "charts": [
                 {"chart_id": "c6", "chart_type": "bar", "title": f"{main_metric} by {cat[0]}",
                  "x_axis": cat[0], "y_axis": main_metric, "color_by": None,
                  "data_columns": [cat[0], main_metric],
                  "position": {"x": 0, "y": 0, "width": 6, "height": 4}, "config": {}},
                 {"chart_id": "c7", "chart_type": "pie", "title": f"Distribution by {cat[0]}",
                  "x_axis": cat[0], "y_axis": main_metric, "color_by": None,
                  "data_columns": [cat[0], main_metric],
                  "position": {"x": 6, "y": 0, "width": 6, "height": 4}, "config": {}}
             ] if cat and main_metric else [], "slicers": []},
            {"page_number": 4, "title": "Performance Analysis", "description": "Comparative performance metrics",
             "charts": [
                 {"chart_id": "c8", "chart_type": "bar", "title": f"Top {cat[0]} by {main_metric}",
                  "x_axis": cat[0], "y_axis": main_metric, "color_by": cat[1] if len(cat) > 1 else None,
                  "data_columns": [c for c in [cat[0], main_metric] if c],
                  "position": {"x": 0, "y": 0, "width": 12, "height": 4}, "config": {}}
             ] if cat and main_metric else [], "slicers": []},
            {"page_number": 5, "title": "Detailed Data", "description": "Full data table",
             "charts": [
                 {"chart_id": "c9", "chart_type": "table", "title": "Data Explorer",
                  "x_axis": None, "y_axis": None, "color_by": None,
                  "data_columns": (num + cat)[:6],
                  "position": {"x": 0, "y": 0, "width": 12, "height": 6}, "config": {}}
             ], "slicers": []},
            {"page_number": 6, "title": "AI Insights", "description": "AI-generated recommendations",
             "charts": [], "slicers": []},
        ]
        return {
            "title": f"{domain.value.title()} Intelligence Dashboard",
            "subtitle": "AI-Generated Executive Dashboard",
            "pages": pages,
            "slicers": [{"column": date, "type": "date_range", "label": "Date Range"}] if date else [],
            "bookmarks": [],
        }
