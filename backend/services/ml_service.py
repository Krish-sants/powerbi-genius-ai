"""ML Service — forecasting, anomaly detection, clustering, regression."""
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from loguru import logger


class MLService:
    def forecast_time_series(
        self, df: pd.DataFrame, date_col: str, value_col: str, periods: int = 12
    ) -> Dict[str, Any]:
        try:
            ts = df[[date_col, value_col]].dropna().sort_values(date_col)
            ts = ts.groupby(date_col)[value_col].sum().reset_index()
            ts.columns = ["ds", "y"]

            if len(ts) < 6:
                return {"error": "Not enough data points for forecasting (min 6)"}

            try:
                from prophet import Prophet
                model = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
                model.fit(ts)
                future = model.make_future_dataframe(periods=periods, freq="MS")
                forecast = model.predict(future)
                return {
                    "method": "prophet",
                    "historical": ts.to_dict(orient="records"),
                    "forecast": forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods).to_dict(orient="records"),
                    "trend": "upward" if forecast["trend"].diff().mean() > 0 else "downward",
                }
            except ImportError:
                pass

            # Fallback: linear regression forecast
            x = np.arange(len(ts))
            y = ts["y"].values
            z = np.polyfit(x, y, 2)
            p = np.poly1d(z)

            future_x = np.arange(len(ts), len(ts) + periods)
            future_y = p(future_x).tolist()

            last_date = pd.to_datetime(ts["ds"].iloc[-1])
            future_dates = pd.date_range(last_date, periods=periods + 1, freq="MS")[1:]

            return {
                "method": "polynomial_regression",
                "historical": ts.to_dict(orient="records"),
                "forecast": [
                    {"ds": str(d.date()), "yhat": round(float(v), 2)}
                    for d, v in zip(future_dates, future_y)
                ],
                "trend": "upward" if z[0] > 0 else "downward",
            }
        except Exception as e:
            logger.error(f"Forecasting error: {e}")
            return {"error": str(e)}

    def detect_anomalies(self, df: pd.DataFrame, columns: List[str]) -> Dict[str, Any]:
        try:
            from sklearn.ensemble import IsolationForest
            from sklearn.preprocessing import StandardScaler

            numeric_data = df[columns].dropna()
            if len(numeric_data) < 10:
                return {"anomaly_count": 0, "anomaly_indices": []}

            scaler = StandardScaler()
            X = scaler.fit_transform(numeric_data)
            iso = IsolationForest(contamination=0.05, random_state=42)
            labels = iso.fit_predict(X)

            anomaly_mask = labels == -1
            anomaly_indices = numeric_data.index[anomaly_mask].tolist()
            anomaly_df = df.loc[anomaly_indices]

            return {
                "anomaly_count": int(anomaly_mask.sum()),
                "anomaly_percentage": round(float(anomaly_mask.mean() * 100), 2),
                "anomaly_indices": anomaly_indices[:50],
                "anomaly_sample": anomaly_df.head(10).to_dict(orient="records"),
            }
        except Exception as e:
            logger.error(f"Anomaly detection error: {e}")
            return {"error": str(e)}

    def cluster_data(self, df: pd.DataFrame, columns: List[str], n_clusters: int = 4) -> Dict[str, Any]:
        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler

            X = df[columns].dropna()
            if len(X) < n_clusters * 2:
                return {"error": "Not enough data for clustering"}

            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(X_scaled)

            df_cluster = X.copy()
            df_cluster["cluster"] = labels
            cluster_summary = df_cluster.groupby("cluster").agg(["mean", "count"]).round(2)

            return {
                "n_clusters": n_clusters,
                "cluster_labels": labels.tolist(),
                "cluster_centers": scaler.inverse_transform(kmeans.cluster_centers_).tolist(),
                "cluster_sizes": pd.Series(labels).value_counts().to_dict(),
                "inertia": round(float(kmeans.inertia_), 2),
            }
        except Exception as e:
            logger.error(f"Clustering error: {e}")
            return {"error": str(e)}

    def compute_correlation_matrix(self, df: pd.DataFrame) -> Dict[str, Any]:
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.shape[1] < 2:
            return {}
        corr = numeric_df.corr().round(3)
        return {
            "columns": list(corr.columns),
            "matrix": corr.values.tolist(),
        }

    def compute_distribution(self, df: pd.DataFrame, column: str, bins: int = 20) -> Dict[str, Any]:
        series = df[column].dropna()
        if not pd.api.types.is_numeric_dtype(series):
            counts = series.value_counts().head(20)
            return {
                "type": "categorical",
                "labels": counts.index.tolist(),
                "values": counts.values.tolist(),
            }
        counts, edges = np.histogram(series, bins=bins)
        return {
            "type": "numeric",
            "bins": [round(float(e), 4) for e in edges[:-1]],
            "counts": counts.tolist(),
            "mean": round(float(series.mean()), 4),
            "median": round(float(series.median()), 4),
            "std": round(float(series.std()), 4),
        }

    def compute_pareto(self, df: pd.DataFrame, category_col: str, value_col: str) -> Dict[str, Any]:
        grouped = df.groupby(category_col)[value_col].sum().sort_values(ascending=False)
        total = grouped.sum()
        cumulative_pct = (grouped.cumsum() / total * 100).round(2)
        pareto_80 = (cumulative_pct <= 80).sum()
        return {
            "categories": grouped.index.tolist()[:20],
            "values": grouped.values.tolist()[:20],
            "cumulative_pct": cumulative_pct.values.tolist()[:20],
            "pareto_80_count": int(pareto_80),
            "pareto_80_pct": round(pareto_80 / len(grouped) * 100, 1),
        }
