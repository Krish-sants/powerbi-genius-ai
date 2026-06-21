from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from datetime import datetime


class DataSourceType(str, Enum):
    FILE = "file"
    URL = "url"
    DATABASE = "database"
    GOOGLE_SHEETS = "google_sheets"
    KAGGLE = "kaggle"
    GITHUB = "github"


class BusinessDomain(str, Enum):
    SALES = "sales"
    FINANCIAL = "financial"
    BANKING = "banking"
    ELECTION = "election"
    HEALTHCARE = "healthcare"
    INSURANCE = "insurance"
    HR = "hr"
    MANUFACTURING = "manufacturing"
    RETAIL = "retail"
    ECOMMERCE = "ecommerce"
    SUPPLY_CHAIN = "supply_chain"
    LOGISTICS = "logistics"
    CUSTOMER = "customer"
    MARKETING = "marketing"
    REAL_ESTATE = "real_estate"
    EDUCATION = "education"
    UNKNOWN = "unknown"


class AgentStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ColumnProfile(BaseModel):
    name: str
    dtype: str
    non_null_count: int
    null_count: int
    null_percentage: float
    unique_count: int
    sample_values: List[Any]
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    mean_value: Optional[float] = None
    std_value: Optional[float] = None
    is_numeric: bool
    is_date: bool
    is_categorical: bool


class DataQualityIssue(BaseModel):
    issue_type: str
    severity: str  # low, medium, high, critical
    column: Optional[str] = None
    description: str
    count: int
    recommendation: str


class OutlierInfo(BaseModel):
    column: str
    method: str
    outlier_count: int
    outlier_percentage: float
    outlier_values: List[float]


class DataQualityReport(BaseModel):
    overall_score: float  # 0-100
    total_rows: int
    total_columns: int
    missing_value_score: float
    duplicate_score: float
    outlier_score: float
    format_score: float
    issues: List[DataQualityIssue]
    outliers: List[OutlierInfo]
    duplicate_count: int
    recommendations: List[str]


class KPIDefinition(BaseModel):
    name: str
    display_name: str
    category: str
    formula: str
    dax_measure: str
    value: Optional[float] = None
    formatted_value: Optional[str] = None
    trend: Optional[str] = None  # up, down, stable
    trend_percentage: Optional[float] = None
    target: Optional[float] = None
    unit: str = ""
    description: str
    priority: int = 1


class Insight(BaseModel):
    insight_id: str
    category: str  # executive, statistical, anomaly, forecast
    title: str
    description: str
    impact: str  # high, medium, low
    metric: Optional[str] = None
    value: Optional[float] = None
    change_percentage: Optional[float] = None
    recommendation: str
    evidence: List[str] = []


class ChartSpec(BaseModel):
    chart_id: str
    chart_type: str  # bar, line, area, pie, scatter, map, gauge, kpi_card, waterfall, funnel
    title: str
    subtitle: Optional[str] = None
    x_axis: Optional[str] = None
    y_axis: Optional[str] = None
    color_by: Optional[str] = None
    size_by: Optional[str] = None
    filters: List[str] = []
    data_columns: List[str] = []
    page: int = 1
    position: Dict[str, int] = {}  # x, y, width, height
    config: Dict[str, Any] = {}


class DashboardPage(BaseModel):
    page_number: int
    title: str
    description: str
    charts: List[ChartSpec]
    slicers: List[str]


class DashboardSpec(BaseModel):
    dashboard_id: str
    title: str
    subtitle: str
    domain: BusinessDomain
    theme: str = "executive_dark"
    pages: List[DashboardPage]
    kpis: List[KPIDefinition]
    insights: List[Insight]
    slicers: List[Dict[str, Any]]
    bookmarks: List[Dict[str, str]]
    color_palette: List[str]
    font_family: str = "Segoe UI"


class DAXMeasure(BaseModel):
    name: str
    expression: str
    table: str
    format_string: Optional[str] = None
    description: str


class DataModel(BaseModel):
    fact_tables: List[str]
    dimension_tables: List[str]
    relationships: List[Dict[str, str]]
    dax_measures: List[DAXMeasure]
    calculated_columns: List[Dict[str, str]]


class AgentState(BaseModel):
    job_id: str
    source_type: DataSourceType
    source_path: Optional[str] = None
    source_url: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None
    cleaned_data: Optional[Dict[str, Any]] = None
    column_profiles: List[ColumnProfile] = []
    domain: Optional[BusinessDomain] = None
    business_context: Optional[str] = None
    data_dictionary: Dict[str, str] = {}
    quality_report: Optional[DataQualityReport] = None
    kpis: List[KPIDefinition] = []
    insights: List[Insight] = []
    dashboard_spec: Optional[DashboardSpec] = None
    data_model: Optional[DataModel] = None
    executive_summary: Optional[str] = None
    narrative: Optional[str] = None
    agent_statuses: Dict[str, AgentStatus] = {}
    errors: List[str] = []
    progress: int = 0
    current_agent: Optional[str] = None


class UploadResponse(BaseModel):
    job_id: str
    message: str
    source_type: DataSourceType
    file_name: Optional[str] = None


class AnalysisStatus(BaseModel):
    job_id: str
    progress: int
    current_agent: Optional[str]
    agent_statuses: Dict[str, str]
    errors: List[str]
    completed: bool
    failed: bool


class NLQueryRequest(BaseModel):
    job_id: str
    query: str
    conversation_history: List[Dict[str, str]] = []


class NLQueryResponse(BaseModel):
    answer: str
    chart_suggestion: Optional[ChartSpec] = None
    data_snippet: Optional[List[Dict[str, Any]]] = None
    follow_up_questions: List[str] = []


class ExportRequest(BaseModel):
    job_id: str
    format: str  # pbix, pdf, ppt, excel, png
    include_insights: bool = True
    include_executive_summary: bool = True
