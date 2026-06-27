// Thin API client for the Radiografia AI backend.
const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const apiBase = () => API;

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("token");
}

export function setToken(token: string) {
  window.localStorage.setItem("token", token);
}

export function clearToken() {
  window.localStorage.removeItem("token");
}

function authHeaders(): Record<string, string> {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function handle(res: Response) {
  if (res.status === 401) {
    clearToken();
    if (typeof window !== "undefined") window.location.href = "/login";
    throw new Error("Não autenticado");
  }
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Erro ${res.status}`);
  }
  return res.json();
}

export async function login(email: string, password: string) {
  const res = await fetch(`${API}/auth/login/json`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await handle(res);
  setToken(data.access_token);
  return data;
}

export interface StudyListItem {
  id: string;
  patient_code: string;
  view: string;
  status: string;
  created_at: string;
  overall_status: string | null;
  priority: "critical" | "routine";
}

export interface Stats {
  total_studies: number;
  by_status: Record<string, number>;
  by_overall_status: Record<string, number>;
  total_reviews: number;
  reviews_with_divergence: number;
  divergence_rate: number;
  mean_inference_time_ms: number;
}

export interface ModelVersion {
  id: string;
  name: string;
  version: string;
  training_dataset: string | null;
  threshold_config: Record<string, number>;
  created_at: string;
}

export interface Finding {
  finding_code: string;
  probability: number;
  threshold: number;
  is_positive: boolean;
  heatmap_url: string | null;
}

export interface Prediction {
  study_id: string;
  prediction_id: string;
  model_version: string;
  overall_status: string;
  inference_time_ms: number;
  findings: Finding[];
  disclaimer: string;
}

export const api = {
  me: () => fetch(`${API}/auth/me`, { headers: authHeaders() }).then(handle),
  listStudies: (): Promise<StudyListItem[]> =>
    fetch(`${API}/studies`, { headers: authHeaders() }).then(handle),
  stats: (): Promise<Stats> =>
    fetch(`${API}/studies/stats`, { headers: authHeaders() }).then(handle),
  modelVersions: (): Promise<ModelVersion[]> =>
    fetch(`${API}/models/versions`, { headers: authHeaders() }).then(handle),
  getStudy: (id: string) =>
    fetch(`${API}/studies/${id}`, { headers: authHeaders() }).then(handle),
  predict: (id: string): Promise<Prediction> =>
    fetch(`${API}/studies/${id}/predict`, { method: "POST", headers: authHeaders() }).then(handle),
  getPrediction: (id: string): Promise<Prediction> =>
    fetch(`${API}/studies/${id}/prediction`, { headers: authHeaders() }).then(handle),
  getReview: (id: string) =>
    fetch(`${API}/studies/${id}/review`, { headers: authHeaders() }).then(handle),
  submitReview: (id: string, payload: unknown) =>
    fetch(`${API}/studies/${id}/review`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify(payload),
    }).then(handle),
  auditTrail: (id: string) =>
    fetch(`${API}/audit/studies/${id}`, { headers: authHeaders() }).then(handle),
  upload: (form: FormData) =>
    fetch(`${API}/studies/upload`, { method: "POST", headers: authHeaders(), body: form }).then(handle),
  imageUrl: (id: string) => `${API}/studies/${id}/image`,
  heatmapUrl: (id: string, code: string) => `${API}/studies/${id}/heatmaps/${code}`,
};
