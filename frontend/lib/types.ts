export interface KPI {
  name: string;
  display_name: string;
  category: string;
  value: number | null;
  formatted_value: string;
  trend?: "up" | "down" | "stable";
  trend_percentage?: number;
  unit: string;
  description: string;
  priority: number;
  dax_measure: string;
}

export interface Insight {
  insight_id: string;
  category: string;
  title: string;
  description: string;
  impact: "high" | "medium" | "low";
  recommendation: string;
  evidence: string[];
  change_percentage?: number;
}

export interface ChartSpec {
  chart_id: string;
  chart_type: string;
  title: string;
  subtitle?: string;
  x_axis?: string;
  y_axis?: string;
  color_by?: string;
  data_columns: string[];
  page: number;
  position: { x: number; y: number; width: number; height: number };
  config: Record<string, unknown>;
}

export interface DashboardPage {
  page_number: number;
  title: string;
  description: string;
  charts: ChartSpec[];
  slicers: string[];
}

export interface DashboardSpec {
  dashboard_id: string;
  title: string;
  subtitle: string;
  domain: string;
  theme: string;
  pages: DashboardPage[];
  kpis: KPI[];
  insights: Insight[];
  slicers: SlicerDef[];
  bookmarks: Bookmark[];
  color_palette: string[];
}

export interface SlicerDef {
  column: string;
  type: string;
  label: string;
}

export interface Bookmark {
  name: string;
  page: string;
}

export interface QualityReport {
  overall_score: number;
  total_rows: number;
  total_columns: number;
  missing_value_score: number;
  duplicate_score: number;
  outlier_score: number;
  format_score: number;
  issues: QualityIssue[];
  duplicate_count: number;
  recommendations: string[];
}

export interface QualityIssue {
  issue_type: string;
  severity: "low" | "medium" | "high" | "critical";
  column?: string;
  description: string;
  count: number;
  recommendation: string;
}

export interface ColumnProfile {
  name: string;
  dtype: string;
  non_null_count: number;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  is_numeric: boolean;
  is_date: boolean;
  is_categorical: boolean;
  mean_value?: number;
  min_value?: number;
  max_value?: number;
}

export interface AgentStatus {
  ingestion_agent: string;
  understanding_agent: string;
  quality_agent: string;
  bi_agent: string;
  insight_agent: string;
  dashboard_agent: string;
}

export interface AnalysisStatus {
  job_id: string;
  progress: number;
  current_agent: string | null;
  agent_statuses: AgentStatus;
  errors: string[];
  completed: boolean;
  failed: boolean;
}

export interface AnalysisResult {
  job_id: string;
  domain: string;
  business_context: string;
  quality_report: QualityReport;
  kpis: KPI[];
  insights: Insight[];
  dashboard_spec: DashboardSpec;
  data_model: DataModel;
  executive_summary: string;
  narrative: string;
  theme: Record<string, string>;
}

export interface DataModel {
  fact_tables: string[];
  dimension_tables: string[];
  relationships: { from: string; to: string; cardinality: string }[];
  dax_measures: DAXMeasure[];
}

export interface DAXMeasure {
  name: string;
  expression: string;
  table: string;
  format_string?: string;
  description: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  chart_suggestion?: ChartSpec;
  follow_up_questions?: string[];
  timestamp: Date;
}
