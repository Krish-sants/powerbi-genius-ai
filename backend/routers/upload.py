import uuid
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, BackgroundTasks
from loguru import logger

from models.schemas import UploadResponse
from agents.ingestion_agent import save_upload
from agents.orchestrator import run_pipeline, set_job
from services.llm_service import get_active_provider

router = APIRouter(prefix="/api/upload", tags=["upload"])


def _check_llm():
    provider = get_active_provider()
    if provider == "none":
        raise HTTPException(status_code=500, detail="No LLM API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env")
    return provider


@router.post("/file", response_model=UploadResponse)
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    _check_llm()
    job_id = str(uuid.uuid4())
    file_bytes = await file.read()
    file_path = await save_upload(file_bytes, file.filename)

    initial_state = {
        "job_id": job_id, "source_type": "file", "source_path": file_path,
        "agent_statuses": {}, "errors": [], "progress": 0,
        "completed": False, "failed": False,
    }
    set_job(job_id, initial_state)
    background_tasks.add_task(run_pipeline, job_id, initial_state)
    logger.info(f"Upload job started: {job_id} — file: {file.filename}")
    return UploadResponse(job_id=job_id, message="File uploaded. Analysis pipeline started.",
                          source_type="file", file_name=file.filename)


@router.post("/url", response_model=UploadResponse)
async def upload_url(background_tasks: BackgroundTasks, url: str = Form(...), source_type: str = Form("url")):
    _check_llm()
    import validators
    if not validators.url(url):
        raise HTTPException(status_code=400, detail="Invalid URL provided")

    job_id = str(uuid.uuid4())
    initial_state = {
        "job_id": job_id, "source_type": source_type, "source_url": url,
        "agent_statuses": {}, "errors": [], "progress": 0,
        "completed": False, "failed": False,
    }
    set_job(job_id, initial_state)
    background_tasks.add_task(run_pipeline, job_id, initial_state)
    return UploadResponse(job_id=job_id, message="URL submitted. Analysis pipeline started.", source_type=source_type)


@router.post("/database", response_model=UploadResponse)
async def upload_database(
    background_tasks: BackgroundTasks,
    connection_string: str = Form(...),
    query: str = Form("SELECT * FROM main_table LIMIT 50000"),
):
    _check_llm()
    job_id = str(uuid.uuid4())
    initial_state = {
        "job_id": job_id, "source_type": "database",
        "connection_string": connection_string, "query": query,
        "agent_statuses": {}, "errors": [], "progress": 0,
        "completed": False, "failed": False,
    }
    set_job(job_id, initial_state)
    background_tasks.add_task(run_pipeline, job_id, initial_state)
    return UploadResponse(job_id=job_id, message="Database connection submitted. Analysis pipeline started.",
                          source_type="database")


@router.post("/multiple", response_model=UploadResponse)
async def upload_multiple(background_tasks: BackgroundTasks, files: list[UploadFile] = File(...)):
    _check_llm()
    job_id = str(uuid.uuid4())
    file_paths = []
    for f in files:
        b = await f.read()
        path = await save_upload(b, f.filename)
        file_paths.append(path)

    initial_state = {
        "job_id": job_id, "source_type": "multiple_files", "source_paths": file_paths,
        "agent_statuses": {}, "errors": [], "progress": 0,
        "completed": False, "failed": False,
    }
    set_job(job_id, initial_state)

    async def _merge_and_run():
        import pandas as pd
        from utils.file_handlers import load_file, clean_column_names, infer_and_cast_types, dataframe_to_dict
        from utils import df_cache
        dfs = []
        for p in file_paths:
            df, _ = await load_file(p)
            dfs.append(df)
        merged = pd.concat(dfs, ignore_index=True)
        merged = clean_column_names(merged)
        merged = infer_and_cast_types(merged)
        df_cache.set_df(job_id, "raw", merged)
        initial_state["raw_data"] = dataframe_to_dict(merged)
        initial_state["agent_statuses"]["ingestion_agent"] = "completed"
        initial_state["progress"] = 15
        set_job(job_id, initial_state)
        await run_pipeline(job_id, initial_state)

    background_tasks.add_task(_merge_and_run)
    return UploadResponse(job_id=job_id,
                          message=f"{len(files)} files uploaded. Merging and starting analysis pipeline.",
                          source_type="file")
