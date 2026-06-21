import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

// Upload endpoints
export const uploadFile = async (file: File): Promise<{ job_id: string }> => {
  const form = new FormData();
  form.append("file", file);
  const { data } = await api.post("/api/upload/file", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

export const uploadUrl = async (url: string, sourceType = "url"): Promise<{ job_id: string }> => {
  const form = new FormData();
  form.append("url", url);
  form.append("source_type", sourceType);
  const { data } = await api.post("/api/upload/url", form);
  return data;
};

export const uploadMultiple = async (files: File[]): Promise<{ job_id: string }> => {
  const form = new FormData();
  files.forEach((f) => form.append("files", f));
  const { data } = await api.post("/api/upload/multiple", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

export const uploadDatabase = async (connectionString: string, query: string): Promise<{ job_id: string }> => {
  const form = new FormData();
  form.append("connection_string", connectionString);
  form.append("query", query);
  const { data } = await api.post("/api/upload/database", form);
  return data;
};

// Analysis endpoints
export const getStatus = async (jobId: string) => {
  const { data } = await api.get(`/api/analysis/status/${jobId}`);
  return data;
};

export const getResult = async (jobId: string) => {
  const { data } = await api.get(`/api/analysis/result/${jobId}`);
  return data;
};

export const getData = async (jobId: string, page = 1, pageSize = 100) => {
  const { data } = await api.get(`/api/analysis/data/${jobId}`, { params: { page, page_size: pageSize } });
  return data;
};

export const getProfile = async (jobId: string) => {
  const { data } = await api.get(`/api/analysis/profile/${jobId}`);
  return data;
};

export const getForecast = async (jobId: string, dateCol?: string, valueCol?: string, periods = 12) => {
  const { data } = await api.get(`/api/analysis/forecast/${jobId}`, {
    params: { date_col: dateCol, value_col: valueCol, periods },
  });
  return data;
};

export const getAnomalies = async (jobId: string) => {
  const { data } = await api.get(`/api/analysis/anomalies/${jobId}`);
  return data;
};

export const getCorrelation = async (jobId: string) => {
  const { data } = await api.get(`/api/analysis/correlation/${jobId}`);
  return data;
};

export const getDistribution = async (jobId: string, column: string) => {
  const { data } = await api.get(`/api/analysis/distribution/${jobId}`, { params: { column } });
  return data;
};

export const getPareto = async (jobId: string, categoryCol: string, valueCol: string) => {
  const { data } = await api.get(`/api/analysis/pareto/${jobId}`, {
    params: { category_col: categoryCol, value_col: valueCol },
  });
  return data;
};

// Chat
export const sendQuery = async (jobId: string, query: string, history: { role: string; content: string }[] = []) => {
  const { data } = await api.post("/api/chat/query", {
    job_id: jobId,
    query,
    conversation_history: history,
  });
  return data;
};

export const getChatSuggestions = async (jobId: string) => {
  const { data } = await api.get(`/api/chat/suggestions/${jobId}`);
  return data;
};

// Export
export const getExportUrl = (jobId: string, format: string) =>
  `${API_BASE}/api/export/${format}/${jobId}`;

// WebSocket helper
export const createProgressWS = (jobId: string, onMessage: (data: unknown) => void): WebSocket => {
  const wsUrl = API_BASE.replace("http", "ws");
  const ws = new WebSocket(`${wsUrl}/ws/progress/${jobId}`);
  ws.onmessage = (e) => {
    try {
      onMessage(JSON.parse(e.data));
    } catch {}
  };
  return ws;
};
