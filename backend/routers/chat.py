"""Natural language query endpoint — chat with your dashboard data."""
import json
import pandas as pd
from fastapi import APIRouter, HTTPException

from agents.orchestrator import get_job
from models.schemas import NLQueryRequest, NLQueryResponse
from services.llm_service import chat_json
from utils import df_cache

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/query", response_model=NLQueryResponse)
async def natural_language_query(request: NLQueryRequest):
    state = get_job(request.job_id)
    if not state:
        raise HTTPException(status_code=404, detail="Job not found")

    cleaned = state.get("cleaned_data", {})
    kpis = state.get("kpis", [])
    insights = state.get("insights", [])
    domain = state.get("domain", "business")
    business_context = state.get("business_context", "")
    data_dict = state.get("data_dictionary", {})

    df = df_cache.get_or_rebuild(request.job_id, "cleaned", cleaned)
    columns = list(df.columns)
    sample = df.head(5).to_dict(orient="records")
    kpi_text = "\n".join([f"- {k.get('display_name')}: {k.get('formatted_value')}" for k in kpis[:6]])
    insight_text = "\n".join([f"- {i.get('title')}" for i in insights[:5]])

    system = f"""You are an expert data analyst for a {domain} dashboard.
Business context: {business_context}
Columns: {columns}
Data dictionary: {json.dumps(data_dict, default=str)}
Key KPIs:
{kpi_text}
Key Insights:
{insight_text}
Sample data: {json.dumps(sample, default=str)}

Answer the user's business question. Be specific and quantified.
Return JSON:
{{
  "answer": "Clear, quantified answer",
  "chart_suggestion": {{"chart_type": "bar", "title": "Chart title", "x_axis": "col", "y_axis": "col", "color_by": null}} or null,
  "follow_up_questions": ["Q1?", "Q2?", "Q3?"]
}}"""

    messages = [{"role": m.get("role", "user"), "content": m.get("content", "")}
                for m in request.conversation_history[-6:]]
    messages.append({"role": "user", "content": request.query})

    data = await chat_json(messages, system=system, max_tokens=1000)

    chart_suggestion = None
    if data.get("chart_suggestion"):
        from models.schemas import ChartSpec
        import uuid
        cs = data["chart_suggestion"]
        chart_suggestion = ChartSpec(
            chart_id=str(uuid.uuid4()),
            chart_type=cs.get("chart_type", "bar"),
            title=cs.get("title", "Chart"),
            x_axis=cs.get("x_axis"),
            y_axis=cs.get("y_axis"),
            color_by=cs.get("color_by"),
            data_columns=[c for c in [cs.get("x_axis"), cs.get("y_axis")] if c],
            page=1,
        )

    return NLQueryResponse(
        answer=data.get("answer", ""),
        chart_suggestion=chart_suggestion,
        follow_up_questions=data.get("follow_up_questions", []),
    )


@router.get("/suggestions/{job_id}")
async def get_query_suggestions(job_id: str):
    state = get_job(job_id)
    if not state:
        raise HTTPException(status_code=404, detail="Job not found")
    domain = state.get("domain", "sales")
    suggestions = {
        "sales": ["What is the total revenue?", "Which product has the highest sales?",
                  "Show revenue trend by month", "Which region performs best?", "What is the average order value?"],
        "financial": ["What is the net profit margin?", "Show expense breakdown", "Which quarter had highest revenue?"],
        "hr": ["What is the attrition rate?", "Show headcount by department", "What is the average salary?"],
        "marketing": ["What is the conversion rate?", "Which channel has best ROI?", "What is the customer acquisition cost?"],
        "healthcare": ["What is the average patient age?", "Show diagnosis distribution", "Which department has most cases?"],
    }
    return {"suggestions": suggestions.get(domain, suggestions["sales"])}
