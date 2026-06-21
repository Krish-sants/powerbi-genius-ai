"""LangGraph orchestrator — wires all 6 agents into a sequential state machine with streaming."""
import asyncio
from typing import Any, Dict
from loguru import logger
from langgraph.graph import StateGraph, END

from agents.ingestion_agent import IngestionAgent
from agents.understanding_agent import UnderstandingAgent
from agents.quality_agent import QualityAgent
from agents.bi_agent import BIAgent
from agents.insight_agent import InsightAgent
from agents.dashboard_agent import DashboardAgent


class PipelineOrchestrator:
    def __init__(self):
        self.ingestion = IngestionAgent()
        self.understanding = UnderstandingAgent()
        self.quality = QualityAgent()
        self.bi = BIAgent()
        self.insight = InsightAgent()
        self.dashboard = DashboardAgent()
        self.graph = self._build_graph()

    def _build_graph(self) -> Any:
        builder = StateGraph(dict)
        builder.add_node("ingest", self._run_ingestion)
        builder.add_node("understand", self._run_understanding)
        builder.add_node("quality", self._run_quality)
        builder.add_node("bi", self._run_bi)
        builder.add_node("insight", self._run_insight)
        builder.add_node("dashboard", self._run_dashboard)
        builder.add_node("finalize", self._finalize)

        builder.set_entry_point("ingest")
        builder.add_edge("ingest", "understand")
        builder.add_edge("understand", "quality")
        builder.add_edge("quality", "bi")
        builder.add_edge("bi", "insight")
        builder.add_edge("insight", "dashboard")
        builder.add_edge("dashboard", "finalize")
        builder.add_edge("finalize", END)
        return builder.compile()

    async def _run_ingestion(self, state: Dict) -> Dict:
        state["current_agent"] = "Data Ingestion Agent"
        state["agent_statuses"]["ingestion_agent"] = "running"
        result = await self.ingestion.run(state)
        set_job(state["job_id"], result)
        return result

    async def _run_understanding(self, state: Dict) -> Dict:
        state["current_agent"] = "Dataset Understanding Agent"
        state["agent_statuses"]["understanding_agent"] = "running"
        result = await self.understanding.run(state)
        set_job(state["job_id"], result)
        return result

    async def _run_quality(self, state: Dict) -> Dict:
        state["current_agent"] = "Data Quality Agent"
        state["agent_statuses"]["quality_agent"] = "running"
        result = await self.quality.run(state)
        set_job(state["job_id"], result)
        return result

    async def _run_bi(self, state: Dict) -> Dict:
        state["current_agent"] = "Business Intelligence Agent"
        state["agent_statuses"]["bi_agent"] = "running"
        result = await self.bi.run(state)
        set_job(state["job_id"], result)
        return result

    async def _run_insight(self, state: Dict) -> Dict:
        state["current_agent"] = "Insight Generation Agent"
        state["agent_statuses"]["insight_agent"] = "running"
        result = await self.insight.run(state)
        set_job(state["job_id"], result)
        return result

    async def _run_dashboard(self, state: Dict) -> Dict:
        state["current_agent"] = "Dashboard Design Agent"
        state["agent_statuses"]["dashboard_agent"] = "running"
        result = await self.dashboard.run(state)
        set_job(state["job_id"], result)
        return result

    async def _finalize(self, state: Dict) -> Dict:
        state["current_agent"] = "Finalizing"
        state["progress"] = 100
        state["completed"] = True
        logger.info(f"[Orchestrator] Job {state['job_id']} completed")
        result = state
        set_job(state["job_id"], result)
        return result

    async def run(self, initial_state: Dict) -> Dict:
        initial_state.setdefault("agent_statuses", {
            "ingestion_agent": "pending", "understanding_agent": "pending",
            "quality_agent": "pending", "bi_agent": "pending",
            "insight_agent": "pending", "dashboard_agent": "pending",
        })
        initial_state.setdefault("errors", [])
        initial_state.setdefault("progress", 0)
        initial_state.setdefault("completed", False)
        return await self.graph.ainvoke(initial_state)


# In-memory job store
_job_store: Dict[str, Dict[str, Any]] = {}


def get_job(job_id: str) -> Dict[str, Any]:
    return _job_store.get(job_id, {})


def set_job(job_id: str, state: Dict[str, Any]) -> None:
    _job_store[job_id] = state


async def run_pipeline(job_id: str, initial_state: Dict) -> None:
    orchestrator = PipelineOrchestrator()
    set_job(job_id, initial_state)
    try:
        result = await orchestrator.run(initial_state)
        set_job(job_id, result)
    except Exception as e:
        logger.error(f"Pipeline failed for job {job_id}: {e}")
        current = get_job(job_id)
        current["failed"] = True
        current["errors"] = current.get("errors", []) + [str(e)]
        set_job(job_id, current)
