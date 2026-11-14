import type {
  AuthResponse,
  AttemptResult,
  LearnGroup,
  LearnModuleDetail,
  PracticeTopic,
  Question,
  Settings,
  User,
} from "./types";

const TOKEN_KEY = "aio-prep-token";

export const getAuthToken = () => localStorage.getItem(TOKEN_KEY);
export const setAuthToken = (token: string) => localStorage.setItem(TOKEN_KEY, token);
export const clearAuthToken = () => localStorage.removeItem(TOKEN_KEY);

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getAuthToken();
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
  });
  if (response.status === 401) {
    clearAuthToken();
    window.dispatchEvent(new Event("auth:unauthorized"));
  }
  if (!response.ok) {
    const raw = await response.text();
    try {
      const parsed = JSON.parse(raw) as { detail?: string };
      throw new Error(parsed.detail || raw);
    } catch (error) {
      if (error instanceof SyntaxError) throw new Error(raw || `${response.status} ${response.statusText}`);
      throw error;
    }
  }
  return response.json() as Promise<T>;
}

export const api = {
  login: (email: string, password: string) =>
    request<AuthResponse>("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  signup: (email: string, password: string, display_name: string) =>
    request<AuthResponse>("/api/auth/signup", {
      method: "POST",
      body: JSON.stringify({ email, password, display_name }),
    }),
  me: () => request<User>("/api/auth/me"),
  googleStatus: () => request<{ configured: boolean }>("/api/auth/google/status"),
  googleStart: () => request<{ url: string }>("/api/auth/google/start"),
  settings: () => request<Settings>("/api/settings"),
  saveSettings: (body: Partial<Settings>) =>
    request<Settings>("/api/settings", { method: "PATCH", body: JSON.stringify(body) }),
  learnModules: () => request<{ groups: LearnGroup[] }>("/api/learn/modules"),
  learnModule: (slug: string) => request<LearnModuleDetail>(`/api/learn/modules/${slug}`),
  completeLesson: (slug: string) => request(`/api/lessons/${slug}/complete`, { method: "POST" }),
  learnCheck: (public_id: string, submitted: string, hints_used = 0) =>
    request<AttemptResult>("/api/learn/check", {
      method: "POST",
      body: JSON.stringify({ public_id, submitted, hints_used }),
    }),
  practiceMeta: () => request<{ topics: PracticeTopic[] }>("/api/practice/meta"),
  nextQuestion: (topic: string, difficulty: "easy" | "medium" | "hard", subtopic?: string) => {
    const params = new URLSearchParams({ topic, difficulty });
    if (subtopic) params.set("subtopic", subtopic);
    return request<Question>(`/api/practice/next?${params}`);
  },
  attempt: (public_id: string, submitted: string, hints_used: number) =>
    request<AttemptResult>("/api/practice/attempt", {
      method: "POST",
      body: JSON.stringify({ public_id, submitted, hints_used }),
    }),
};
