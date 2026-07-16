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
    if (typeof window !== "undefined") {
      const next = `${window.location.pathname}${window.location.search}`;
      window.location.href = `/login?next=${encodeURIComponent(next)}`;
    }
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

export interface ClinicalPolicyRule {
  finding_code: string;
  label: string;
  critical: boolean;
  worklist_priority: "critical" | "routine";
  requires_human_review: boolean;
  action: string;
}

export interface ClinicalPolicy {
  id: string;
  name: string;
  version: string;
  scope: string;
  status: string;
  active: boolean;
  modality: string[];
  body_part: string;
  clinical_output: string;
  human_review_required: boolean;
  autonomous_diagnosis_allowed: boolean;
  finalization_rule: string;
  critical_findings: string[];
  rule_guardrails: Record<string, unknown>;
  rules: ClinicalPolicyRule[];
  created_at: string;
  updated_at: string | null;
  activated_at: string | null;
  created_by_user_id: string | null;
  notes: string | null;
}

export interface DivergenceBucket {
  reviewed_findings: number;
  divergences: number;
  divergence_rate: number;
}

export interface CriticalDivergenceCase {
  study_id: string;
  review_id: string;
  finding_code: string;
  decision: string;
  model_version: string;
  clinical_policy_version: string;
  reviewed_at: string;
}

export interface DivergenceReport {
  filters: {
    from: string | null;
    to: string | null;
    model_version: string | null;
    clinical_policy_version: string | null;
  };
  summary: {
    reviewed_studies: number;
    reviews: number;
    reviewed_findings: number;
    divergences: number;
    divergence_rate: number;
    critical_divergences: number;
  };
  by_decision: Record<string, number>;
  by_finding: Record<string, DivergenceBucket>;
  by_model_version: Record<string, DivergenceBucket>;
  by_clinical_policy: Record<string, DivergenceBucket>;
  critical_divergence_cases: CriticalDivergenceCase[];
}

export interface DivergenceFilters {
  from?: string;
  to?: string;
  model_version?: string;
  clinical_policy_version?: string;
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
  activePolicy: (): Promise<ClinicalPolicy> =>
    fetch(`${API}/models/policy/active`, { headers: authHeaders() }).then(handle),
  clinicalPolicies: (): Promise<ClinicalPolicy[]> =>
    fetch(`${API}/models/policies`, { headers: authHeaders() }).then(handle),
  divergenceReport: (filters: DivergenceFilters = {}): Promise<DivergenceReport> => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.set(key, value);
    });
    const query = params.toString();
    return fetch(`${API}/governance/divergence${query ? `?${query}` : ""}`, { headers: authHeaders() }).then(handle);
  },
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
