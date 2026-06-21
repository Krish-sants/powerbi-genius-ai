import os
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from loguru import logger
import asyncio
import json

# Explicitly load .env from the project root (one level above backend/)
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=True)

from routers import upload, analysis, export, chat
from agents.orchestrator import get_job

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("PowerBI Genius AI Backend starting up...")
    os.makedirs("./uploads", exist_ok=True)
    os.makedirs("./exports", exist_ok=True)
    yield
    logger.info("PowerBI Genius AI Backend shutting down...")


app = FastAPI(
    title="PowerBI Genius AI",
    description="Autonomous AI Agent for Power BI Dashboard Generation",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(export.router)
app.include_router(chat.router)


@app.get("/health")
async def health():
    ant_key = os.getenv("ANTHROPIC_API_KEY", "")
    oai_key = os.getenv("OPENAI_API_KEY", "")
    return {
        "status": "healthy", "service": "PowerBI Genius AI", "version": "1.0.0",
        "anthropic_key": f"{ant_key[:12]}...{ant_key[-4:]}" if ant_key else "NOT SET",
        "openai_key": f"{oai_key[:12]}...{oai_key[-4:]}" if oai_key else "NOT SET",
        "env_path": str(_env_path),
        "env_exists": _env_path.exists(),
    }


@app.websocket("/ws/progress/{job_id}")
async def websocket_progress(websocket: WebSocket, job_id: str):
    await websocket.accept()
    logger.info(f"WebSocket connected for job: {job_id}")
    try:
        last_progress = -1
        while True:
            state = get_job(job_id)
            if not state:
                await websocket.send_json({"error": "Job not found"})
                break

            progress = state.get("progress", 0)
            current_agent = state.get("current_agent", "")
            agent_statuses = state.get("agent_statuses", {})
            errors = state.get("errors", [])
            completed = state.get("completed", False)
            failed = state.get("failed", False)

            if progress != last_progress or completed or failed:
                await websocket.send_json({
                    "job_id": job_id,
                    "progress": progress,
                    "current_agent": current_agent,
                    "agent_statuses": agent_statuses,
                    "errors": errors,
                    "completed": completed,
                    "failed": failed,
                })
                last_progress = progress

            if completed or failed:
                break

            await asyncio.sleep(1)
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for job: {job_id}")
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
        try:
            await websocket.send_json({"error": str(e)})
        except Exception:
            pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
