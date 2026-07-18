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
  Sparkles,
  Settings2
} from "lucide-react";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import { CardSkeleton } from "@/components/ui/skeleton";

export default function BrainSettingsPage() {
  const { data: brain, loading } = useApi({
    fetcher: () => api.getBrain(),
    errorMessage: "Failed to load Brain settings",
  });

  const agents = [
    { name: "Developer Agent", status: "ready", tasks: 142, icon: Cpu, color: "text-ion", bg: "bg-[var(--ion-dim)]" },
    { name: "Research Agent", status: "ready", tasks: 89, icon: Brain, color: "text-ion", bg: "bg-[var(--ion-dim)]" },
    { name: "Security Agent", status: "ready", tasks: 24, icon: Shield, color: "text-teal", bg: "bg-[var(--teal-dim)]" },
    { name: "QA Agent", status: "ready", tasks: 56, icon: Zap, color: "text-signal", bg: "bg-[var(--signal-dim)]" },
    { name: "Project Manager", status: "ready", tasks: 211, icon: Users, color: "text-ion", bg: "bg-[var(--ion-dim)]" },
    { name: "Documentation", status: "ready", tasks: 45, icon: Bot, color: "text-teal", bg: "bg-[var(--teal-dim)]" },
    { name: "Infrastructure", status: "ready", tasks: 12, icon: Server, color: "text-signal", bg: "bg-[var(--signal-dim)]" },
    { name: "Business Agent", status: "ready", tasks: 8, icon: Activity, color: "text-teal", bg: "bg-[var(--teal-dim)]" },
  ];

  const modules = [
    { name: "Memory Engine", desc: "Persistent memory with RAG", enabled: true, icon: Layers },
    { name: "Reasoning Engine", desc: "Multi-step reasoning & planning", enabled: true, icon: Brain },
    { name: "Learning Engine", desc: "Adapts to your preferences", enabled: true, icon: Sparkles },
    { name: "Planning Engine", desc: "Goal decomposition & execution", enabled: true, icon: Activity },
    { name: "Agent Orchestrator", desc: "Coordinates specialized agents", enabled: true, icon: Users },
    { name: "Knowledge Engine", desc: "Document indexing & search", enabled: true, icon: Bot },
  ];

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-bone tracking-tight flex items-center gap-3 font-display">
            Brain Settings
            <div className="status-dot w-2 h-2 rounded-full bg-teal ml-2" />
          </h1>
          <p className="text-sm text-soft mt-1">
            Configure your AI Brain — agents, modules, and core capabilities
          </p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2.5 bg-panel/50 hover:bg-panel-2 text-soft border border-hairline rounded-xl font-medium text-sm transition-all shadow-sm">
          <Settings2 className="w-4 h-4" />
          Advanced
        </button>
      </div>

      {loading ? (
        <div className="space-y-6">
          <CardSkeleton />
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <CardSkeleton /><CardSkeleton /><CardSkeleton /><CardSkeleton />
          </div>
        </div>
      ) : (
        <>
          {/* Brain overview */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="instrument border-hairline rounded-2xl p-6 relative overflow-hidden"
          >
            <div className="absolute top-0 right-0 w-64 h-64 bg-[var(--ion-dim)] rounded-full blur-[80px] pointer-events-none" />
            <div className="absolute bottom-0 left-0 w-64 h-64 bg-[var(--teal-dim)] rounded-full blur-[80px] pointer-events-none" />

            <div className="flex items-center gap-4 mb-8 relative z-10">
              <div className="w-14 h-14 rounded-2xl bg-[var(--gradient-primary)] p-[1px] shadow-[var(--shadow-glow)]">
                <div className="w-full h-full bg-ink rounded-[15px] flex items-center justify-center">
                  <Brain className="w-7 h-7 text-bone brain-glow" />
                </div>
              </div>
              <div>
                <h2 className="text-xl font-bold text-bone tracking-tight">
                  {brain?.name || "AGI Core"}
                </h2>
                <p className="text-sm text-soft flex items-center gap-2 mt-1">
                  Status: <span className="text-teal font-medium capitalize flex items-center gap-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-teal status-dot" />
                    {brain?.status || "Active"}
                  </span>
                </p>
              </div>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 relative z-10">
              <div className="bg-panel/50 border border-hairline rounded-xl p-4 text-center glass hover:bg-panel-2/30 transition-colors">
                <p className="text-2xl font-bold text-bone tracking-tight font-display">{brain?.stats?.total_conversations ?? 0}</p>
                <p className="text-xs font-medium text-muted uppercase tracking-wider mt-1 font-mono">Conversations</p>
              </div>
              <div className="bg-panel/50 border border-hairline rounded-xl p-4 text-center glass hover:bg-panel-2/30 transition-colors">
                <p className="text-2xl font-bold text-bone tracking-tight font-display">{brain?.stats?.total_memories ?? 0}</p>
                <p className="text-xs font-medium text-muted uppercase tracking-wider mt-1 font-mono">Memories</p>
              </div>
              <div className="bg-panel/50 border border-hairline rounded-xl p-4 text-center glass hover:bg-panel-2/30 transition-colors">
                <p className="text-2xl font-bold text-bone tracking-tight font-display">{brain?.stats?.total_tasks ?? 0}</p>
                <p className="text-xs font-medium text-muted uppercase tracking-wider mt-1 font-mono">Tasks</p>
              </div>
              <div className="bg-panel/50 border border-hairline rounded-xl p-4 text-center glass hover:bg-panel-2/30 transition-colors">
                <p className="text-2xl font-bold text-bone tracking-tight font-display">8</p>
                <p className="text-xs font-medium text-muted uppercase tracking-wider mt-1 font-mono">Active Agents</p>
              </div>
            </div>
          </motion.div>

          {/* Agents */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-bone flex items-center gap-2">
              <Bot className="w-5 h-5 text-ion" />
              Specialized AI Agents
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {agents.map((agent, i) => {
                const Icon = agent.icon;
                return (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05 }}
                    key={agent.name}
                    className="instrument border-hairline rounded-2xl p-5 group hover:border-hairline-strong transition-colors"
                  >
                    <div className="flex items-center gap-3 mb-4">
                      <div className={`w-10 h-10 rounded-xl ${agent.bg} flex items-center justify-center border border-white/5`}>
                        <Icon className={`w-5 h-5 ${agent.color}`} />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-bone leading-tight">{agent.name}</p>
                        <div className="flex items-center gap-1.5 mt-1">
                          <div className="w-1.5 h-1.5 rounded-full bg-teal shadow-[0_0_8px_rgba(53,208,186,0.5)]" />
                          <span className="text-[10px] font-medium text-soft uppercase tracking-wider">{agent.status}</span>
                        </div>
                      </div>
                    </div>
                    <div className="pt-3 border-t border-hairline flex items-center justify-between">
                      <span className="text-xs text-muted font-medium">Tasks Completed</span>
                      <span className="text-sm font-bold text-soft font-mono">{agent.tasks}</span>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>

          {/* Modules */}
          <div className="space-y-4">
            <h2 className="text-lg font-semibold text-bone flex items-center gap-2">
              <Layers className="w-5 h-5 text-teal" />
              Brain Modules
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {modules.map((mod, i) => {
                const Icon = mod.icon;
                return (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.05 }}
                    key={mod.name}
                    className="instrument border-hairline rounded-2xl p-5 flex items-center justify-between group hover:border-hairline-strong transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 rounded-xl bg-panel-2 flex items-center justify-center border border-hairline group-hover:border-hairline-strong transition-colors">
                        <Icon className="w-5 h-5 text-soft group-hover:text-bone transition-colors" />
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-bone">{mod.name}</p>
                        <p className="text-xs text-muted mt-0.5 font-medium">{mod.desc}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-5 rounded-full relative cursor-pointer transition-colors shadow-inner ${mod.enabled ? 'bg-teal' : 'bg-panel-2'}`}>
                        <div className={`w-3.5 h-3.5 bg-bone rounded-full absolute top-[3px] transition-all shadow-sm ${mod.enabled ? 'right-1' : 'left-1'}`} />
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
