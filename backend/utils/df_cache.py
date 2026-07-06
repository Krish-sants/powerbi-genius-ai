"""In-memory per-job DataFrame cache.

Agents and routers share the actual DataFrame objects instead of round-tripping
the dataset through ``to_dict(orient="records")`` → ``pd.DataFrame(...)`` at
every step. The records dict kept in job state is only a (capped) preview for
API responses; anything analytical should go through this cache. Rebuilding
from records is kept as a fallback so old jobs / process restarts still work.
"""
from typing import Any, Dict, Optional

import pandas as pd

_cache: Dict[str, Dict[str, pd.DataFrame]] = {}


def set_df(job_id: str, key: str, df: pd.DataFrame) -> None:
    _cache.setdefault(job_id, {})[key] = df


def get_df(job_id: str, key: str) -> Optional[pd.DataFrame]:
    return _cache.get(job_id, {}).get(key)


def get_or_rebuild(job_id: str, key: str, records_dict: Optional[Dict[str, Any]]) -> pd.DataFrame:
    """Return the cached DataFrame, falling back to rebuilding from a records dict."""
    df = get_df(job_id, key)
    if df is not None:
        return df
    records = (records_dict or {}).get("data", [])
    return pd.DataFrame(records)


def clear_job(job_id: str) -> None:
    _cache.pop(job_id, None)
