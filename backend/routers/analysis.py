import pandas as pd
from fastapi import APIRouter, HTTPException
from typing import Any, Dict, List

from agents.orchestrator import get_job
from models.schemas import AnalysisStatus
from services.ml_service import MLService
from utils import df_cache

router = APIRouter(prefix="/api/analysis", tags=["analysis"])
ml = MLService()


def _get_state(job_id: str) -> Dict[str, Any]:
    state = get_job(job_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return state


def _get_cleaned_df(job_id: str, state: Dict[str, Any]) -> pd.DataFrame:
    return df_cache.get_or_rebuild(
        job_id, "cleaned", state.get("cleaned_data") or state.get("raw_data")
    )


@router.get("/status/{job_id}", response_model=AnalysisStatus)
async def get_status(job_id: str):
    state = _get_state(job_id)
    return AnalysisStatus(
        job_id=job_id,
        progress=state.get("progress", 0),
        current_agent=state.get("current_agent"),
        agent_statuses={k: str(v) for k, v in state.get("agent_statuses", {}).items()},
        errors=state.get("errors", []),
        completed=state.get("completed", False),
        failed=state.get("failed", False),
    )


@router.get("/result/{job_id}")
async def get_result(job_id: str):
    state = _get_state(job_id)
    if not state.get("completed"):
        raise HTTPException(status_code=202, detail="Analysis still in progress")
    return {
        "job_id": job_id,
        "domain": state.get("domain"),
        "business_context": state.get("business_context"),
        "quality_report": state.get("quality_report"),
        "kpis": state.get("kpis", []),
        "insights": state.get("insights", []),
        "dashboard_spec": state.get("dashboard_spec"),
        "data_model": state.get("data_model"),
        "executive_summary": state.get("executive_summary"),
        "narrative": state.get("narrative"),
        "theme": state.get("theme"),
    }


@router.get("/data/{job_id}")
async def get_data(job_id: str, page: int = 1, page_size: int = 100):
    state = _get_state(job_id)
    df = _get_cleaned_df(job_id, state)
    total = len(df)
    start = (page - 1) * page_size
    return {
        "columns": list(df.columns),
        "data": df.iloc[start:start + page_size].to_dict(orient="records"),
        "total": total,
        "page": page,
        "pages": (total + page_size - 1) // page_size,
    }


@router.get("/profile/{job_id}")
async def get_profile(job_id: str):
    state = _get_state(job_id)
    return {
        "column_profiles": state.get("column_profiles", []),
        "data_dictionary": state.get("data_dictionary", {}),
        "entity_mapping": state.get("entity_mapping", {}),
        "quality_report": state.get("quality_report"),
    }


@router.get("/forecast/{job_id}")
async def get_forecast(job_id: str, date_col: str = None, value_col: str = None, periods: int = 12):
    state = _get_state(job_id)
    df = _get_cleaned_df(job_id, state)
    if df.empty:
        raise HTTPException(status_code=400, detail="No cleaned data available")

    if not date_col:
        date_cols = df.select_dtypes(include=["datetime64"]).columns.tolist()
        if not date_cols:
            # Try to find date-like columns
            for col in df.columns:
                try:
                    pd.to_datetime(df[col], errors="raise")
                    df[col] = pd.to_datetime(df[col])
                    date_col = col
                    break
                except Exception:
                    pass
        else:
            date_col = date_cols[0]

    if not value_col:
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        if not numeric_cols:
            raise HTTPException(status_code=400, detail="No numeric columns for forecasting")
        value_col = numeric_cols[0]

    if date_col and date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    result = ml.forecast_time_series(df, date_col, value_col, periods)
    return {"date_col": date_col, "value_col": value_col, "periods": periods, **result}


@router.get("/anomalies/{job_id}")
async def get_anomalies(job_id: str):
    state = _get_state(job_id)
    df = _get_cleaned_df(job_id, state)
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()[:6]
    if not numeric_cols:
        return {"anomaly_count": 0, "message": "No numeric columns"}
    return ml.detect_anomalies(df, numeric_cols)


@router.get("/correlation/{job_id}")
async def get_correlation(job_id: str):
    state = _get_state(job_id)
    df = _get_cleaned_df(job_id, state)
    return ml.compute_correlation_matrix(df)


@router.get("/distribution/{job_id}")
async def get_distribution(job_id: str, column: str):
    state = _get_state(job_id)
    df = _get_cleaned_df(job_id, state)
    if column not in df.columns:
        raise HTTPException(status_code=400, detail=f"Column {column} not found")
    return ml.compute_distribution(df, column)


@router.get("/pareto/{job_id}")
async def get_pareto(job_id: str, category_col: str, value_col: str):
    state = _get_state(job_id)
    df = _get_cleaned_df(job_id, state)
    if category_col not in df.columns or value_col not in df.columns:
        raise HTTPException(status_code=400, detail="Column not found")
    return ml.compute_pareto(df, category_col, value_col)
