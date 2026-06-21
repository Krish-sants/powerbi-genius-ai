import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, JSONResponse

from agents.orchestrator import get_job
from models.schemas import ExportRequest
from services.export_service import ExportService
from services.dax_generator import generate_measures_for_dataset, generate_full_dax_script
from models.schemas import DAXMeasure

router = APIRouter(prefix="/api/export", tags=["export"])
exporter = ExportService()


def _require_completed(job_id: str) -> dict:
    state = get_job(job_id)
    if not state:
        raise HTTPException(status_code=404, detail="Job not found")
    if not state.get("completed"):
        raise HTTPException(status_code=202, detail="Analysis still in progress")
    return state


@router.get("/excel/{job_id}")
async def export_excel(job_id: str):
    state = _require_completed(job_id)
    data = exporter.export_excel(state)
    domain = state.get("domain", "dashboard").replace(" ", "_")
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="powerbi_genius_{domain}_report.xlsx"'},
    )


@router.get("/pdf/{job_id}")
async def export_pdf(job_id: str):
    state = _require_completed(job_id)
    data = exporter.export_pdf(state)
    domain = state.get("domain", "dashboard").replace(" ", "_")
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="powerbi_genius_{domain}_report.pdf"'},
    )


@router.get("/pptx/{job_id}")
async def export_pptx(job_id: str):
    state = _require_completed(job_id)
    data = exporter.export_pptx(state)
    domain = state.get("domain", "dashboard").replace(" ", "_")
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="powerbi_genius_{domain}_presentation.pptx"'},
    )


@router.get("/pbix-template/{job_id}")
async def export_pbix_template(job_id: str):
    state = _require_completed(job_id)
    template = exporter.generate_pbix_template(state)
    domain = state.get("domain", "dashboard").replace(" ", "_")
    json_bytes = json.dumps(template, indent=2, default=str).encode("utf-8")
    return Response(
        content=json_bytes,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="powerbi_genius_{domain}_template.json"'},
    )


@router.get("/dax/{job_id}")
async def export_dax(job_id: str):
    state = _require_completed(job_id)
    data_model = state.get("data_model", {})
    raw_measures = data_model.get("dax_measures", [])
    measures = [DAXMeasure(**m) if isinstance(m, dict) else m for m in raw_measures]
    script = generate_full_dax_script(measures)
    return Response(
        content=script.encode("utf-8"),
        media_type="text/plain",
        headers={"Content-Disposition": 'attachment; filename="powerbi_genius_dax_measures.dax"'},
    )


@router.get("/csv/{job_id}")
async def export_cleaned_csv(job_id: str):
    import pandas as pd
    import io
    state = _require_completed(job_id)
    cleaned = state.get("cleaned_data", state.get("raw_data", {}))
    df = pd.DataFrame(cleaned.get("data", []))
    domain = state.get("domain", "data").replace(" ", "_")
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="powerbi_genius_{domain}_cleaned.csv"'},
    )
