// In production (no NEXT_PUBLIC_API_URL), use same-origin proxy via vercel.json rewrite.
// In development, set NEXT_PUBLIC_API_URL=http://localhost:8000 in .env.local.
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("brain_token") : null;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    if (res.status === 401 && typeof window !== "undefined") {
      // Auto-logout on 401 Unauthorized
      localStorage.removeItem("brain_token");
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `API error: ${res.status}`);
  }

  return res.json();
}

// Auth
export const api = {
  // Auth
  register: (email: string, password: string, full_name?: string) =>
    request<{ token: string; user_id: string; email: string }>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),

  login: (email: string, password: string) =>
    request<{ token: string; user_id: string; email: string }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  getMe: () => request<{ id: string; email: string; full_name: string | null; role: string; is_mfa_enabled: boolean }>("/api/auth/me"),

  // Brain
  getBrain: () => request<{
    id: string;
    name: string;
    status: string;
    stats: { total_conversations: number; total_memories: number; total_tasks: number };
    settings: Record<string, unknown>;
  }>("/api/brain/"),

  // Conversations
  getConversations: (limit = 20) =>
    request<{ id: string; title: string; summary: string | null; updated_at: string }[]>(
      `/api/brain/conversations?limit=${limit}`
    ),

  // Chat
  chat: (message: string, conversation_id?: string) =>
    request<{ conversation_id: string; response: string }>("/api/brain/chat", {
      method: "POST",
      body: JSON.stringify({ message, conversation_id }),
    }),

  getMessages: (conversationId: string) =>
    request<{ id: string; role: string; content: string; created_at: string }[]>(
      `/api/brain/conversations/${conversationId}/messages`
    ),

  // Memories
  getMemories: (type?: string) =>
    request<{ id: string; title: string; memory_type: string; summary: string; created_at: string }[]>(
      `/api/memory/${type ? `?memory_type=${type}` : ""}`
    ),

  searchMemories: (query: string) =>
    request<{ id: string; title: string; content: string; memory_type: string }[]>(
      `/api/memory/search?query=${encodeURIComponent(query)}`
    ),

  storeMemory: (data: { memory_type: string; title: string; content: string; importance?: string }) =>
    request<{ id: string; title: string }>("/api/memory/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  // Tasks
  getTasks: (status?: string) =>
    request<{ id: string; title: string; status: string; priority: string; created_at: string }[]>(
      `/api/tasks/${status ? `?status=${status}` : ""}`
    ),

  createTask: (data: { title: string; description?: string; priority?: string }) =>
    request<{ id: string; title: string; status: string }>("/api/tasks/", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getGoals: () =>
    request<{ id: string; title: string; status: string; progress: number }[]>("/api/tasks/goals"),
};
