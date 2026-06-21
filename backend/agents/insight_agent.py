"""Agent 5: Insight Generation Agent — executive insights, AI narratives, forecasting, anomaly detection."""
import json
import uuid
import numpy as np
import pandas as pd
from typing import Any, Dict, List
from loguru import logger

from models.schemas import Insight, BusinessDomain
from services.llm_service import chat_json


class InsightAgent:
    name = "insight_agent"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[InsightAgent] Starting for job {state['job_id']}")
        try:
            df = pd.DataFrame(state["cleaned_data"]["data"])
            domain = state.get("domain", "unknown")
            kpis = state.get("kpis", [])
            data_dict = state.get("data_dictionary", {})
            business_context = state.get("business_context", "")

            stat_insights = self._compute_statistical_insights(df)
            forecast_insights = self._compute_forecast_insights(df)
            anomaly_insights = self._compute_anomaly_insights(df)
            ai_insights = await self._generate_ai_insights(df, domain, kpis, data_dict, business_context)

            all_insights = stat_insights + forecast_insights + anomaly_insights + ai_insights
            state["insights"] = [i.dict() for i in all_insights]

            exec_summary = await self._generate_executive_summary(
                domain, kpis, all_insights, business_context, df.shape
            )
            state["executive_summary"] = exec_summary.get("summary", "")
            state["narrative"] = exec_summary.get("narrative", "")

            state["agent_statuses"]["insight_agent"] = "completed"
            state["progress"] = 75
            logger.info(f"[InsightAgent] Generated {len(all_insights)} insights")
        except Exception as e:
            logger.error(f"[InsightAgent] Error: {e}")
            state["agent_statuses"]["insight_agent"] = "failed"
            state["errors"].append(f"Insight error: {str(e)}")
        return state

    def _compute_statistical_insights(self, df: pd.DataFrame) -> List[Insight]:
        insights = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        for col in numeric_cols[:5]:
            series = df[col].dropna()
            if len(series) < 2: continue
            mean, std = series.mean(), series.std()
            cv = std / abs(mean) * 100 if mean != 0 else 0
            if cv > 50:
                insights.append(Insight(
                    insight_id=str(uuid.uuid4()), category="statistical",
                    title=f"High Variability in {col}",
                    description=f"{col} shows high variability (CV={cv:.1f}%). Range: {series.min():.2f} to {series.max():.2f}.",
                    impact="medium", metric=col,
                    recommendation="Investigate root causes of variance and consider segmented analysis.",
                    evidence=[f"Mean: {mean:.2f}", f"Std Dev: {std:.2f}", f"CV: {cv:.1f}%"],
                ))
        if len(numeric_cols) >= 2:
            corr = df[numeric_cols[:8]].corr()
            for i, col1 in enumerate(numeric_cols[:8]):
                for col2 in numeric_cols[i+1:8]:
                    r = corr.loc[col1, col2]
                    if abs(r) > 0.7:
                        direction = "positive" if r > 0 else "negative"
                        insights.append(Insight(
                            insight_id=str(uuid.uuid4()), category="statistical",
                            title=f"Strong {direction.title()} Correlation: {col1} vs {col2}",
                            description=f"{col1} and {col2} have a strong {direction} correlation (r={r:.2f}).",
                            impact="high" if abs(r) > 0.85 else "medium",
                            recommendation=f"Leverage the {direction} relationship for predictive modeling.",
                            evidence=[f"Pearson r = {r:.3f}"],
                        ))
        return insights[:6]

    def _compute_forecast_insights(self, df: pd.DataFrame) -> List[Insight]:
        insights = []
        date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not date_cols or not numeric_cols: return insights
        try:
            date_col, metric_col = date_cols[0], numeric_cols[0]
            ts = df[[date_col, metric_col]].dropna().sort_values(date_col)
            ts = ts.groupby(date_col)[metric_col].sum().reset_index()
            if len(ts) >= 6:
                x, y = np.arange(len(ts)), ts[metric_col].values
                z = np.polyfit(x, y, 1)
                trend_pct = (z[0] * len(ts)) / abs(y.mean()) * 100 if y.mean() != 0 else 0
                trend_dir = "upward" if z[0] > 0 else "downward"
                insights.append(Insight(
                    insight_id=str(uuid.uuid4()), category="forecast",
                    title=f"{metric_col} shows {trend_dir} trajectory ({abs(trend_pct):.1f}%)",
                    description=f"{metric_col} has a {trend_dir} trend of {abs(trend_pct):.1f}% over the analysis period.",
                    impact="high", metric=metric_col, change_percentage=round(trend_pct, 2),
                    recommendation="Capitalize on growth momentum." if z[0] > 0 else "Investigate declining trend.",
                    evidence=[f"Linear slope: {z[0]:.4f}", f"Projected trend: {trend_pct:.1f}%"],
                ))
        except Exception as e:
            logger.warning(f"Forecast insight error: {e}")
        return insights

    def _compute_anomaly_insights(self, df: pd.DataFrame) -> List[Insight]:
        insights = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if not numeric_cols: return insights
        try:
            from sklearn.ensemble import IsolationForest
            X = df[numeric_cols[:5]].dropna()
            if len(X) >= 20:
                labels = IsolationForest(contamination=0.05, random_state=42).fit_predict(X)
                count = int((labels == -1).sum())
                pct = count / len(X) * 100
                if count > 0:
                    insights.append(Insight(
                        insight_id=str(uuid.uuid4()), category="anomaly",
                        title=f"Anomaly Alert: {count} Unusual Records Detected",
                        description=f"{count} records ({pct:.1f}%) show unusual patterns across {', '.join(numeric_cols[:5])}.",
                        impact="high" if pct > 5 else "medium",
                        recommendation="Review flagged records for data quality issues or exceptional business events.",
                        evidence=[f"Anomaly count: {count}", f"Rate: {pct:.1f}%"],
                    ))
        except Exception as e:
            logger.warning(f"Anomaly insight error: {e}")
        return insights

    async def _generate_ai_insights(
        self, df: pd.DataFrame, domain: str, kpis: List[Dict],
        data_dict: Dict, business_context: str
    ) -> List[Insight]:
        kpi_summary = [{"name": k.get("display_name"), "value": k.get("formatted_value")} for k in kpis[:6]]
        sample = df.head(10).to_dict(orient="records")

        prompt = f"""You are a senior McKinsey business analyst. Generate 5 executive insights for a {domain} dataset.

Business context: {business_context}
KPIs: {json.dumps(kpi_summary, default=str)}
Sample data: {json.dumps(sample, default=str)}
Dataset shape: {df.shape[0]} rows x {df.shape[1]} columns

Generate 5 specific, quantified executive insights. Return JSON:
{{
  "insights": [
    {{
      "title": "Specific insight title with numbers",
      "description": "Detailed description with metrics",
      "impact": "high",
      "category": "revenue",
      "recommendation": "Specific action to take",
      "evidence": ["Metric 1: value", "Metric 2: value"]
    }}
  ]
}}"""

        result = await chat_json([{"role": "user", "content": prompt}])
        return [
            Insight(
                insight_id=str(uuid.uuid4()),
                category="executive",
                title=i.get("title", ""),
                description=i.get("description", ""),
                impact=i.get("impact", "medium"),
                recommendation=i.get("recommendation", ""),
                evidence=i.get("evidence", []),
            )
            for i in result.get("insights", [])
        ]

    async def _generate_executive_summary(
        self, domain: str, kpis: List[Dict], insights: List[Insight],
        business_context: str, shape: tuple
    ) -> Dict[str, str]:
        kpi_text = "\n".join([f"- {k.get('display_name')}: {k.get('formatted_value')}" for k in kpis[:6]])
        insight_text = "\n".join([f"- {i.title}: {i.description}" for i in insights[:5]])

        prompt = f"""You are a McKinsey Partner writing a board-level executive summary.

Domain: {domain}
Dataset: {shape[0]:,} rows x {shape[1]} columns
Business Context: {business_context}
Key KPIs:
{kpi_text}
Key Insights:
{insight_text}

Write an executive summary and strategic narrative. Return JSON:
{{
  "summary": "4-5 paragraph executive summary covering situation, key findings, risks, and recommendations",
  "narrative": "Storytelling narrative answering: What happened? Why? What should we do next?"
}}"""

        return await chat_json([{"role": "user", "content": prompt}], max_tokens=6000)
