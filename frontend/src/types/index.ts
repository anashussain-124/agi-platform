export type User = {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  created_at: string;
};

export type Brain = {
  id: string;
  name: string;
  status: string;
  stats: {
    total_conversations: number;
    total_memories: number;
    total_tasks: number;
  };
  preferences: Record<string, unknown>;
  settings: {
    auto_learn: boolean;
    auto_index: boolean;
    require_approval_deploy: boolean;
    require_approval_write: boolean;
  };
};

export type Conversation = {
  id: string;
  title: string;
  summary: string | null;
  updated_at: string;
  created_at: string;
};

export type Message = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
};

export type MemoryEntry = {
  id: string;
  memory_type: string;
  importance: string;
  title: string;
  summary: string;
  source: string | null;
  tags: Record<string, unknown>;
  created_at: string;
};

export type Task = {
  id: string;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  assigned_agent: string | null;
  requires_approval: boolean;
  created_at: string;
};

export type Goal = {
  id: string;
  title: string;
  description: string | null;
  status: string;
  progress: number;
  milestones: string[];
  created_at: string;
};
