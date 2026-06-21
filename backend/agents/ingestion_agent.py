"""Agent 1: Data Ingestion Agent — accepts all data sources and returns a clean DataFrame."""
import os
import uuid
import aiofiles
import pandas as pd
from pathlib import Path
from typing import Any, Dict, Optional
from loguru import logger

from utils.file_handlers import (
    load_file, load_from_url, clean_column_names,
    infer_and_cast_types, dataframe_to_dict
)


UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class IngestionAgent:
    name = "ingestion_agent"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[IngestionAgent] Starting for job {state['job_id']}")
        try:
            df = await self._load_data(state)
            df = clean_column_names(df)
            df = infer_and_cast_types(df)
            df = df.dropna(how="all").reset_index(drop=True)

            state["raw_data"] = dataframe_to_dict(df)
            state["agent_statuses"]["ingestion_agent"] = "completed"
            state["progress"] = 15
            logger.info(f"[IngestionAgent] Loaded {df.shape[0]} rows x {df.shape[1]} cols")
        except Exception as e:
            logger.error(f"[IngestionAgent] Error: {e}")
            state["agent_statuses"]["ingestion_agent"] = "failed"
            state["errors"].append(f"Ingestion error: {str(e)}")
        return state

    async def _load_data(self, state: Dict[str, Any]) -> pd.DataFrame:
        source_type = state.get("source_type", "file")

        if source_type == "file":
            path = state.get("source_path")
            if not path:
                raise ValueError("No file path provided")
            df, _ = await load_file(path)
            return df

        elif source_type in ("url", "kaggle", "github"):
            url = state.get("source_url")
            if not url:
                raise ValueError("No URL provided")
            # Handle Kaggle dataset URL
            if "kaggle.com" in url:
                url = self._transform_kaggle_url(url)
            # Handle GitHub raw
            if "github.com" in url and "/blob/" in url:
                url = url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            return await load_from_url(url)

        elif source_type == "google_sheets":
            url = state.get("source_url", "")
            csv_url = url.replace("/edit#gid=", "/export?format=csv&gid=")
            if "/edit" not in csv_url:
                csv_url = csv_url.rstrip("/") + "/export?format=csv"
            return await load_from_url(csv_url)

        elif source_type == "database":
            return await self._load_from_database(state)

        else:
            raise ValueError(f"Unknown source type: {source_type}")

    def _transform_kaggle_url(self, url: str) -> str:
        # Attempt to build a direct download URL — requires user to have set API credentials
        parts = url.rstrip("/").split("/")
        try:
            idx = parts.index("datasets")
            owner = parts[idx + 1]
            dataset = parts[idx + 2]
            return f"https://www.kaggle.com/datasets/{owner}/{dataset}/download"
        except (ValueError, IndexError):
            return url

    async def _load_from_database(self, state: Dict[str, Any]) -> pd.DataFrame:
        from sqlalchemy import create_engine, text
        conn_str = state.get("connection_string", "")
        query = state.get("query", "SELECT * FROM information_schema.tables LIMIT 100")
        engine = create_engine(conn_str)
        with engine.connect() as conn:
            return pd.read_sql(text(query), conn)


async def save_upload(file_bytes: bytes, filename: str) -> str:
    safe_name = f"{uuid.uuid4()}_{Path(filename).name}"
    dest = UPLOAD_DIR / safe_name
    async with aiofiles.open(dest, "wb") as f:
        await f.write(file_bytes)
    return str(dest)
