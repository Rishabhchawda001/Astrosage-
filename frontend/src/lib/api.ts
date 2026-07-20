// ── AstroSage API Client ──

import type {
  SearchRequest, SearchResponse,
  AnswerRequest, AnswerResponse,
  EntityDetail, EntitySummary, ScriptureSummary, PathResult, GraphStats,
  ChatCompletionsRequest, TokenResponse, RegisterRequest, UserResponse,
  Conversation, Message, CacheStats, HealthResponse,
} from "@/types/api";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

// ── Token Management ──

function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("astrosage_access_token");
}

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("astrosage_refresh_token");
}

export function setTokens(access: string, refresh: string) {
  localStorage.setItem("astrosage_access_token", access);
  localStorage.setItem("astrosage_refresh_token", refresh);
}

export function clearTokens() {
  localStorage.removeItem("astrosage_access_token");
  localStorage.removeItem("astrosage_refresh_token");
  localStorage.removeItem("astrosage_user");
}

export function isAuthenticated(): boolean {
  return !!getAccessToken();
}

// ── Fetch Wrapper ──

class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function refreshAccessToken(): Promise<boolean> {
  const refresh = getRefreshToken();
  if (!refresh) return false;

  try {
    const res = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return false;
    const data: TokenResponse = await res.json();
    setTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  auth = true
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (auth) {
    const token = getAccessToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  let res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  // Try token refresh on 401
  if (res.status === 401 && auth) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      const newToken = getAccessToken();
      headers["Authorization"] = `Bearer ${newToken}`;
      res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    }
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const error = body?.error || body;
    throw new ApiError(
      res.status,
      error?.code || "unknown",
      error?.message || `HTTP ${res.status}`,
      error?.details
    );
  }

  return res.json();
}

// ── Auth API ──

export const auth = {
  login(username: string, password: string) {
    return request<TokenResponse>("/api/v1/auth/token", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }, false);
  },

  register(data: RegisterRequest) {
    return request<UserResponse>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    }, false);
  },

  me() {
    return request<UserResponse>("/api/v1/auth/me");
  },

  createApiKey() {
    return request<{ api_key: string }>("/api/v1/auth/api-keys", {
      method: "POST",
    });
  },
};

// ── Search API ──

export const search = {
  query(data: SearchRequest) {
    return request<SearchResponse>("/api/v1/search", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  quick(q: string, top_k = 10) {
    return request<SearchResponse>(`/api/v1/search?q=${encodeURIComponent(q)}&top_k=${top_k}`);
  },
};

// ── Answer API ──

export const answer = {
  ask(data: AnswerRequest) {
    return request<AnswerResponse>("/api/v1/answer", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
};

// ── Graph API ──

export const graph = {
  entity(name: string) {
    return request<EntityDetail>(`/api/v1/graph/entity/${encodeURIComponent(name)}`);
  },

  searchEntities(q: string, limit = 10) {
    return request<EntitySummary[]>(`/api/v1/graph/search?q=${encodeURIComponent(q)}&limit=${limit}`);
  },

  scriptures() {
    return request<ScriptureSummary[]>("/api/v1/graph/scriptures");
  },

  scripture(id: string) {
    return request<ScriptureSummary>(`/api/v1/graph/scripture/${encodeURIComponent(id)}`);
  },

  path(source: string, target: string, maxDepth = 3) {
    return request<PathResult>(
      `/api/v1/graph/path?source=${encodeURIComponent(source)}&target=${encodeURIComponent(target)}&max_depth=${maxDepth}`
    );
  },

  stats() {
    return request<GraphStats>("/api/v1/graph/stats");
  },
};

// ── Chat API (SSE Streaming) ──

export function chatStream(
  body: ChatCompletionsRequest,
  onToken: (token: string) => void,
  onDone: () => void,
  onError: (err: Error) => void,
  abortSignal?: AbortSignal
): () => void {
  const controller = new AbortController();
  const signal = abortSignal || controller.signal;

  (async () => {
    try {
      const token = getAccessToken();
      const headers: Record<string, string> = {
        "Content-Type": "application/json",
      };
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const res = await fetch(`${API_BASE}/api/v1/chat/completions`, {
        method: "POST",
        headers,
        body: JSON.stringify({ ...body, stream: true }),
        signal,
      });

      if (!res.ok) {
        const errBody = await res.json().catch(() => ({}));
        onError(new Error(errBody?.error?.message || `HTTP ${res.status}`));
        return;
      }

      const reader = res.body?.getReader();
      if (!reader) {
        onError(new Error("No response body"));
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6).trim();
            if (data === "[DONE]") {
              onDone();
              return;
            }
            try {
              const parsed = JSON.parse(data);
              const content = parsed?.choices?.[0]?.delta?.content || "";
              if (content) onToken(content);
              if (parsed?.choices?.[0]?.finish_reason === "stop") {
                onDone();
                return;
              }
            } catch {
              // Skip malformed JSON
            }
          }
        }
      }
      onDone();
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        onError(err as Error);
      }
    }
  })();

  return () => controller.abort();
}

// ── Conversations API ──

export const conversations = {
  list() {
    return request<Conversation[]>("/api/v1/conversations");
  },

  get(id: string) {
    return request<Conversation>(`/api/v1/conversations/${id}`);
  },

  create(model = "gpt-4o-mini") {
    return request<Conversation>("/api/v1/conversations", {
      method: "POST",
      body: JSON.stringify({ model }),
    });
  },

  getMessages(id: string) {
    return request<Message[]>(`/api/v1/conversations/${id}/messages`);
  },

  addMessage(id: string, role: string, content: string) {
    return request<Message>(`/api/v1/conversations/${id}/messages`, {
      method: "POST",
      body: JSON.stringify({ role, content }),
    });
  },

  updateTitle(id: string, title: string) {
    return request<void>(`/api/v1/conversations/${id}/title`, {
      method: "PATCH",
      body: JSON.stringify({ title }),
    });
  },

  delete(id: string) {
    return request<void>(`/api/v1/conversations/${id}`, {
      method: "DELETE",
    });
  },
};

// ── Health API ──

export const health = {
  check() {
    return request<HealthResponse>("/api/v1/health", {}, false);
  },
};

// ── Cache API ──

export const cache = {
  stats() {
    return request<CacheStats>("/api/v1/cache/stats");
  },

  clear() {
    return request<void>("/api/v1/cache/clear", { method: "POST" });
  },
};
