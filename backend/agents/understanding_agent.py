"""Agent 2: Dataset Understanding Agent — detects domain, builds data dictionary, maps entities."""
import json
import pandas as pd
from typing import Any, Dict, List
from loguru import logger

from models.schemas import BusinessDomain, ColumnProfile
from services.llm_service import chat_json


DOMAIN_KEYWORDS = {
    BusinessDomain.SALES: ["revenue", "sales", "order", "product", "customer", "deal", "pipeline", "quota", "discount", "invoice"],
    BusinessDomain.FINANCIAL: ["profit", "loss", "ebitda", "balance", "asset", "liability", "equity", "cash flow", "budget", "expense", "income"],
    BusinessDomain.BANKING: ["loan", "deposit", "interest", "credit", "debit", "transaction", "account", "npa", "emi", "bank"],
    BusinessDomain.HEALTHCARE: ["patient", "diagnosis", "treatment", "hospital", "drug", "prescription", "doctor", "disease", "icd", "claim"],
    BusinessDomain.HR: ["employee", "headcount", "attrition", "salary", "department", "hire", "termination", "performance", "leave", "payroll"],
    BusinessDomain.MARKETING: ["campaign", "impression", "click", "conversion", "ctr", "cpc", "lead", "funnel", "channel", "roi"],
    BusinessDomain.RETAIL: ["store", "sku", "inventory", "pos", "basket", "shelf", "shrinkage", "footfall", "merchandising"],
    BusinessDomain.ECOMMERCE: ["cart", "checkout", "return", "refund", "session", "bounce", "gmv", "aov", "fulfillment"],
    BusinessDomain.SUPPLY_CHAIN: ["supplier", "purchase order", "lead time", "warehouse", "shipment", "vendor", "procurement", "bom"],
    BusinessDomain.LOGISTICS: ["shipment", "delivery", "route", "fleet", "tracking", "freight", "carrier", "pod", "dispatch"],
    BusinessDomain.MANUFACTURING: ["production", "oee", "downtime", "defect", "yield", "shift", "machine", "scrap", "capacity"],
    BusinessDomain.INSURANCE: ["policy", "premium", "claim", "insured", "actuary", "loss ratio", "underwriting", "coverage"],
    BusinessDomain.REAL_ESTATE: ["property", "listing", "rent", "mortgage", "sqft", "valuation", "lease", "occupancy", "tenant"],
    BusinessDomain.EDUCATION: ["student", "grade", "course", "enrollment", "attendance", "exam", "score", "teacher", "school"],
    BusinessDomain.ELECTION: ["vote", "candidate", "constituency", "party", "ballot", "election", "poll", "result", "seat"],
    BusinessDomain.CUSTOMER: ["customer", "churn", "retention", "lifetime", "segment", "nps", "satisfaction", "loyalty", "cohort"],
}


class UnderstandingAgent:
    name = "understanding_agent"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[UnderstandingAgent] Starting for job {state['job_id']}")
        try:
            raw_data = state.get("raw_data", {})
            columns = raw_data.get("columns", [])
            dtypes = raw_data.get("dtypes", {})
            sample = raw_data.get("data", [])[:5]

            profiles = await self._build_profiles(raw_data)
            state["column_profiles"] = [p.dict() for p in profiles]

            domain = self._detect_domain(columns, sample)
            state["domain"] = domain.value

            dict_result = await self._generate_data_dictionary(columns, dtypes, sample, domain)
            state["data_dictionary"] = dict_result.get("dictionary", {})
            state["business_context"] = dict_result.get("context", "")
            state["entity_mapping"] = dict_result.get("entities", {})

            state["agent_statuses"]["understanding_agent"] = "completed"
            state["progress"] = 30
            logger.info(f"[UnderstandingAgent] Domain detected: {domain.value}")
        except Exception as e:
            logger.error(f"[UnderstandingAgent] Error: {e}")
            state["agent_statuses"]["understanding_agent"] = "failed"
            state["errors"].append(f"Understanding error: {str(e)}")
        return state

    def _detect_domain(self, columns: List[str], sample: List[Dict]) -> BusinessDomain:
        col_text = " ".join(c.lower().replace("_", " ") for c in columns)
        sample_text = " ".join(str(v).lower() for row in sample for v in row.values())
        combined = col_text + " " + sample_text
        scores: Dict[BusinessDomain, int] = {}
        for domain, keywords in DOMAIN_KEYWORDS.items():
            scores[domain] = sum(1 for kw in keywords if kw in combined)
        best = max(scores, key=lambda d: scores[d])
        return best if scores[best] > 0 else BusinessDomain.UNKNOWN

    async def _build_profiles(self, raw_data: Dict[str, Any]) -> List[ColumnProfile]:
        df = pd.DataFrame(raw_data.get("data", []))
        profiles = []
        for col in df.columns:
            series = df[col]
            is_numeric = pd.api.types.is_numeric_dtype(series)
            is_date = pd.api.types.is_datetime64_any_dtype(series)
            is_cat = not is_numeric and not is_date and series.nunique() < 50
            profiles.append(ColumnProfile(
                name=col, dtype=str(series.dtype),
                non_null_count=int(series.notna().sum()),
                null_count=int(series.isna().sum()),
                null_percentage=round(series.isna().mean() * 100, 2),
                unique_count=int(series.nunique()),
                sample_values=series.dropna().head(5).tolist(),
                min_value=float(series.min()) if is_numeric else None,
                max_value=float(series.max()) if is_numeric else None,
                mean_value=float(series.mean()) if is_numeric else None,
                std_value=float(series.std()) if is_numeric else None,
                is_numeric=is_numeric, is_date=is_date, is_categorical=is_cat,
            ))
        return profiles

    async def _generate_data_dictionary(
        self, columns: List[str], dtypes: Dict, sample: List[Dict], domain: BusinessDomain
    ) -> Dict[str, Any]:
        sample_str = json.dumps(sample[:3], default=str, indent=2)
        prompt = f"""You are a senior business intelligence consultant.
Analyze this dataset and provide a data dictionary, business context, and entity mapping.

Dataset domain: {domain.value}
Columns: {columns}
Data types: {dtypes}
Sample rows:
{sample_str}

Respond in this exact JSON format:
{{
  "dictionary": {{"column_name": "business description"}},
  "context": "2-3 sentence business context",
  "entities": {{"fact_columns": [], "dimension_columns": [], "date_columns": [], "metric_columns": []}}
}}"""

        return await chat_json([{"role": "user", "content": prompt}])
