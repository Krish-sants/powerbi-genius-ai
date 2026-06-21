"""Agent 3: Data Quality Agent — missing values, duplicates, outliers, validation, quality score."""
import numpy as np
import pandas as pd
from typing import Any, Dict, List
from loguru import logger
from sklearn.ensemble import IsolationForest
from scipy import stats

from models.schemas import DataQualityReport, DataQualityIssue, OutlierInfo


class QualityAgent:
    name = "quality_agent"

    async def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[QualityAgent] Starting for job {state['job_id']}")
        try:
            df = pd.DataFrame(state["raw_data"]["data"])
            report = self._analyze(df)

            # Clean data
            df_clean = self._clean(df, report)
            state["cleaned_data"] = {
                "columns": list(df_clean.columns),
                "dtypes": {col: str(dtype) for col, dtype in df_clean.dtypes.items()},
                "shape": list(df_clean.shape),
                "data": df_clean.to_dict(orient="records"),
            }
            state["quality_report"] = report.dict()
            state["agent_statuses"]["quality_agent"] = "completed"
            state["progress"] = 45
            logger.info(f"[QualityAgent] Quality score: {report.overall_score:.1f}")
        except Exception as e:
            logger.error(f"[QualityAgent] Error: {e}")
            state["agent_statuses"]["quality_agent"] = "failed"
            state["errors"].append(f"Quality error: {str(e)}")
            state["cleaned_data"] = state.get("raw_data", {})
        return state

    def _analyze(self, df: pd.DataFrame) -> DataQualityReport:
        issues: List[DataQualityIssue] = []
        outliers: List[OutlierInfo] = []

        # --- Missing Values ---
        missing_score = 100.0
        for col in df.columns:
            null_pct = df[col].isna().mean() * 100
            if null_pct > 0:
                severity = "low" if null_pct < 5 else "medium" if null_pct < 20 else "high" if null_pct < 50 else "critical"
                issues.append(DataQualityIssue(
                    issue_type="missing_values",
                    severity=severity,
                    column=col,
                    description=f"{col} has {null_pct:.1f}% missing values ({int(df[col].isna().sum())} rows)",
                    count=int(df[col].isna().sum()),
                    recommendation=f"Impute with {'mean/median' if df[col].dtype != object else 'mode or Unknown'}"
                ))
                missing_score -= null_pct * 0.5
        missing_score = max(0, missing_score)

        # --- Duplicates ---
        dup_count = int(df.duplicated().sum())
        dup_pct = dup_count / max(len(df), 1) * 100
        dup_score = max(0, 100 - dup_pct * 2)
        if dup_count > 0:
            issues.append(DataQualityIssue(
                issue_type="duplicates",
                severity="medium" if dup_pct < 10 else "high",
                description=f"{dup_count} duplicate rows ({dup_pct:.1f}%)",
                count=dup_count,
                recommendation="Remove exact duplicate rows"
            ))

        # --- Outliers ---
        outlier_score = 100.0
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        for col in numeric_cols[:10]:  # cap for performance
            series = df[col].dropna()
            if len(series) < 10:
                continue

            # IQR method
            q1, q3 = series.quantile(0.25), series.quantile(0.75)
            iqr = q3 - q1
            iqr_outliers = series[(series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)]

            # Z-Score method
            z_scores = np.abs(stats.zscore(series))
            zscore_outliers = series[z_scores > 3]

            outlier_vals = list(set(iqr_outliers.tolist() + zscore_outliers.tolist()))[:10]
            if outlier_vals:
                outlier_pct = len(outlier_vals) / len(series) * 100
                outliers.append(OutlierInfo(
                    column=col,
                    method="IQR+ZScore",
                    outlier_count=len(outlier_vals),
                    outlier_percentage=round(outlier_pct, 2),
                    outlier_values=[round(float(v), 4) for v in outlier_vals[:5]],
                ))
                outlier_score -= outlier_pct * 0.3
        outlier_score = max(0, outlier_score)

        # --- Format Validation ---
        format_score = 100.0
        for col in df.columns:
            if df[col].dtype == object:
                sample = df[col].dropna().head(100)
                # Check for mixed types
                numeric_count = pd.to_numeric(sample, errors="coerce").notna().sum()
                if 0 < numeric_count < len(sample) * 0.8:
                    issues.append(DataQualityIssue(
                        issue_type="mixed_types",
                        severity="medium",
                        column=col,
                        description=f"{col} appears to have mixed numeric/text values",
                        count=int(numeric_count),
                        recommendation="Standardize column type"
                    ))
                    format_score -= 5

        overall = (missing_score * 0.35 + dup_score * 0.25 + outlier_score * 0.25 + format_score * 0.15)
        recommendations = [
            "Remove duplicate rows before analysis",
            "Impute missing values using domain-appropriate strategies",
            "Review and cap extreme outliers in numeric columns",
            "Standardize date formats to ISO 8601",
            "Encode categorical variables consistently",
        ]

        return DataQualityReport(
            overall_score=round(overall, 1),
            total_rows=len(df),
            total_columns=len(df.columns),
            missing_value_score=round(missing_score, 1),
            duplicate_score=round(dup_score, 1),
            outlier_score=round(outlier_score, 1),
            format_score=round(format_score, 1),
            issues=issues[:20],
            outliers=outliers,
            duplicate_count=dup_count,
            recommendations=recommendations,
        )

    def _clean(self, df: pd.DataFrame, report: DataQualityReport) -> pd.DataFrame:
        # Remove duplicates
        df = df.drop_duplicates().reset_index(drop=True)

        # Impute missing values
        for col in df.columns:
            if df[col].isna().any():
                if pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(df[col].median())
                else:
                    mode = df[col].mode()
                    fill_val = mode[0] if not mode.empty else "Unknown"
                    df[col] = df[col].fillna(fill_val)

        return df
