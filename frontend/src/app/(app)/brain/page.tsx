"use client";

import { useState, useEffect } from "react";
import {
  Brain,
  Cpu,
  Shield,
  Zap,
  Activity,
  Users,
  Server,
  Bot,
  Layers,
} from "lucide-react";
import { api } from "@/lib/api";

export default function BrainSettingsPage() {
  const [brain, setBrain] = useState<{
    name: string;
    status: string;
    stats: { total_conversations: number; total_memories: number; total_tasks: number };
    settings: Record<string, unknown>;
  } | null>(null);

  useEffect(() => {
    api.getBrain().then(setBrain).catch(() => {});
  }, []);

  const agents = [
    { name: "Developer Agent", status: "ready", tasks: 0, icon: Cpu },
    { name: "Research Agent", status: "ready", tasks: 0, icon: Brain },
    { name: "Security Agent", status: "ready", tasks: 0, icon: Shield },
    { name: "QA Agent", status: "ready", tasks: 0, icon: Zap },
    { name: "Project Manager", status: "ready", tasks: 0, icon: Users },
    { name: "Documentation Agent", status: "ready", tasks: 0, icon: Bot },
    { name: "Infrastructure Agent", status: "ready", tasks: 0, icon: Server },
    { name: "Business Agent", status: "ready", tasks: 0, icon: Activity },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-zinc-100">Brain Settings</h1>
        <p className="text-sm text-zinc-500 mt-1">
          Configure your AI Brain — agents, modules, and capabilities
        </p>
      </div>

      {/* Brain overview */}
      <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-teal-500 flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-zinc-200">
              {brain?.name || "Your Brain"}
            </h2>
            <p className="text-xs text-zinc-500">
              Status: <span className="text-teal-400">{brain?.status || "active"}</span>
            </p>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
            <p className="text-lg font-bold text-zinc-100">{brain?.stats?.total_conversations ?? 0}</p>
            <p className="text-xs text-zinc-500">Conversations</p>
          </div>
          <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
            <p className="text-lg font-bold text-zinc-100">{brain?.stats?.total_memories ?? 0}</p>
            <p className="text-xs text-zinc-500">Memories</p>
          </div>
          <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
            <p className="text-lg font-bold text-zinc-100">{brain?.stats?.total_tasks ?? 0}</p>
            <p className="text-xs text-zinc-500">Tasks</p>
          </div>
          <div className="bg-zinc-800/50 rounded-lg p-3 text-center">
            <p className="text-lg font-bold text-zinc-100">8</p>
            <p className="text-xs text-zinc-500">Active Agents</p>
          </div>
        </div>
      </div>

      {/* Agents */}
      <div>
        <h2 className="text-sm font-semibold text-zinc-300 mb-3 flex items-center gap-2">
          <Bot className="w-4 h-4 text-violet-400" />
          Specialized AI Agents
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
          {agents.map((agent) => {
            const Icon = agent.icon;
            return (
              <div
                key={agent.name}
                className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 hover:border-zinc-700 transition-colors"
              >
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center">
                    <Icon className="w-4 h-4 text-violet-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-zinc-200">{agent.name}</p>
                    <div className="flex items-center gap-1.5">
                      <div className="w-1.5 h-1.5 rounded-full bg-teal-500" />
                      <span className="text-[10px] text-zinc-500">{agent.status}</span>
                    </div>
                  </div>
                </div>
                <p className="text-xs text-zinc-600">{agent.tasks} tasks completed</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Modules */}
      <div>
        <h2 className="text-sm font-semibold text-zinc-300 mb-3 flex items-center gap-2">
          <Layers className="w-4 h-4 text-teal-400" />
          Brain Modules
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {[
            { name: "Memory Engine", desc: "Persistent memory with RAG", enabled: true },
            { name: "Reasoning Engine", desc: "Multi-step reasoning & planning", enabled: true },
            { name: "Learning Engine", desc: "Adapts to your preferences", enabled: true },
            { name: "Planning Engine", desc: "Goal decomposition & execution", enabled: true },
            { name: "Agent Orchestrator", desc: "Coordinates specialized agents", enabled: true },
            { name: "Knowledge Engine", desc: "Document indexing & search", enabled: true },
          ].map((mod) => (
            <div
              key={mod.name}
              className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 flex items-center justify-between"
            >
              <div>
                <p className="text-sm font-medium text-zinc-200">{mod.name}</p>
                <p className="text-xs text-zinc-500 mt-0.5">{mod.desc}</p>
              </div>
              <div
                className={`w-2 h-2 rounded-full ${
                  mod.enabled ? "bg-teal-500" : "bg-zinc-600"
                }`}
              />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
