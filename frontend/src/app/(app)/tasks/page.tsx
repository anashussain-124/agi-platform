"use client";

import { useState, useEffect } from "react";
import {
  ListChecks,
  Plus,
  Target,
  Clock,
  AlertCircle,
  CheckCircle2,
  Play,
  Brain,
  Zap,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import { ListItemSkeleton } from "@/components/ui/skeleton";
import { showToast } from "@/components/ui/toast";

const statusColors: Record<string, string> = {
  pending: "bg-zinc-800/50 text-zinc-400 border-zinc-700",
  in_progress: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  completed: "bg-teal-500/10 text-teal-400 border-teal-500/20",
  failed: "bg-red-500/10 text-red-400 border-red-500/20",
  cancelled: "bg-zinc-800/50 text-zinc-500 border-zinc-700",
  approval_needed: "bg-amber-500/10 text-amber-400 border-amber-500/20",
};

const priorityColors: Record<string, string> = {
  low: "text-zinc-500 font-medium",
  medium: "text-amber-400 font-medium",
  high: "text-red-400 font-semibold",
  critical: "text-red-500 font-bold",
};

export default function TasksPage() {
  const [showCreate, setShowCreate] = useState(false);
  const [newTask, setNewTask] = useState({ title: "", description: "", priority: "medium" });
  const [tab, setTab] = useState<"tasks" | "goals">("tasks");
  const [isCreating, setIsCreating] = useState(false);

  // Data fetching
  const { 
    data: tasks = [], 
    loading: tasksLoading, 
    refetch: fetchTasks 
  } = useApi({
    fetcher: () => api.getTasks(),
    errorMessage: "Failed to load tasks",
  });

  const { 
    data: goals = [], 
    loading: goalsLoading, 
    refetch: fetchGoals 
  } = useApi({
    fetcher: () => api.getGoals(),
    errorMessage: "Failed to load goals",
  });

  const handleCreate = async () => {
    if (!newTask.title.trim()) {
      showToast("Please provide a task title", "error");
      return;
    }
    
    setIsCreating(true);
    try {
      await api.createTask(newTask);
      showToast("Task created successfully", "success");
      setShowCreate(false);
      setNewTask({ title: "", description: "", priority: "medium" });
      fetchTasks();
    } catch (err: any) {
      showToast(err.message || "Failed to create task", "error");
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            Tasks & Goals
            <div className="status-pulse w-2 h-2 rounded-full bg-violet-400 ml-2" />
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Plan, execute, and track progress with your Brain
          </p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium text-sm transition-all shadow-sm
            ${showCreate 
              ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700" 
              : "bg-[var(--gradient-primary)] text-zinc-950 hover:opacity-90 shadow-[var(--shadow-glow)]"
            }`}
        >
          <Plus className={`w-4 h-4 transition-transform ${showCreate ? "rotate-45" : ""}`} />
          {showCreate ? "Cancel" : "New Task"}
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 glass p-1.5 rounded-xl w-fit border border-zinc-800/50">
        <button
          onClick={() => setTab("tasks")}
          className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 ${
            tab === "tasks" 
              ? "bg-zinc-800 text-white shadow-sm" 
              : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
          }`}
        >
          <ListChecks className={`w-4 h-4 ${tab === "tasks" ? "text-violet-400" : ""}`} />
          Tasks
        </button>
        <button
          onClick={() => setTab("goals")}
          className={`px-5 py-2 rounded-lg text-sm font-semibold transition-all flex items-center gap-2 ${
            tab === "goals" 
              ? "bg-zinc-800 text-white shadow-sm" 
              : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50"
          }`}
        >
          <Target className={`w-4 h-4 ${tab === "goals" ? "text-teal-400" : ""}`} />
          Goals
        </button>
      </div>

      {/* Create task form */}
      <AnimatePresence>
        {showCreate && (
          <motion.div
            initial={{ opacity: 0, height: 0, y: -20 }}
            animate={{ opacity: 1, height: "auto", y: 0 }}
            exit={{ opacity: 0, height: 0, y: -20 }}
            className="overflow-hidden"
          >
            <div className="glass-strong border-zinc-800/50 rounded-2xl p-5 space-y-4 shadow-lg mb-6">
              <input
                type="text"
                value={newTask.title}
                onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
                placeholder="Task title..."
                className="w-full bg-zinc-900/50 border border-zinc-800/80 rounded-xl px-4 py-3 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-violet-500 transition-all"
                disabled={isCreating}
              />
              <textarea
                value={newTask.description}
                onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
                placeholder="What needs to be done?"
                rows={3}
                className="w-full bg-zinc-900/50 border border-zinc-800/80 rounded-xl px-4 py-3 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-violet-500 transition-all resize-none custom-scrollbar"
                disabled={isCreating}
              />
              <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-medium text-zinc-500 uppercase tracking-wider">Priority:</span>
                  <select
                    value={newTask.priority}
                    onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
                    className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-300 focus:outline-none focus:ring-1 focus:ring-violet-500"
                    disabled={isCreating}
                  >
                    <option value="low">Low Priority</option>
                    <option value="medium">Medium Priority</option>
                    <option value="high">High Priority</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                <button
                  onClick={handleCreate}
                  disabled={isCreating}
                  className="px-6 py-2 bg-[var(--gradient-primary)] text-zinc-950 text-sm font-semibold rounded-xl transition-all shadow-[var(--shadow-glow)] disabled:opacity-50 hover:opacity-90"
                >
                  {isCreating ? "Creating..." : "Create Task"}
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="relative">
        <AnimatePresence mode="wait">
          {tab === "tasks" ? (
            /* Tasks List */
            <motion.div 
              key="tasks"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 10 }}
              transition={{ duration: 0.2 }}
              className="space-y-3"
            >
              {tasksLoading ? (
                // Loading Skeletons
                <>
                  <ListItemSkeleton />
                  <ListItemSkeleton />
                  <ListItemSkeleton />
                </>
              ) : tasks && tasks.length === 0 ? (
                <div className="text-center py-16 glass rounded-2xl border-dashed border-zinc-800">
                  <div className="w-16 h-16 rounded-full bg-zinc-900 flex items-center justify-center mx-auto mb-4 shadow-inner">
                    <ListChecks className="w-8 h-8 text-zinc-600" />
                  </div>
                  <p className="text-zinc-400 font-medium">No tasks yet</p>
                  <button
                    onClick={() => setShowCreate(true)}
                    className="text-sm text-violet-400 hover:text-violet-300 mt-2 font-medium transition-colors"
                  >
                    Create your first task
                  </button>
                </div>
              ) : (
                tasks?.map((task: any, i: number) => (
                  <motion.div
                    key={task.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05, duration: 0.3 }}
                    className="glass card-hover border-zinc-800/50 rounded-2xl p-4 md:p-5 group"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="flex items-start gap-4">
                        <div
                          className={`w-3 h-3 rounded-full mt-1.5 shrink-0 ${
                            task.status === "completed"
                              ? "bg-teal-400 shadow-[0_0_8px_rgba(45,212,191,0.5)]"
                              : task.status === "in_progress"
                              ? "bg-blue-400 shadow-[0_0_8px_rgba(96,165,250,0.5)] animate-pulse"
                              : task.status === "failed"
                              ? "bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]"
                              : "bg-zinc-600"
                          }`}
                        />
                        <div>
                          <h3 className="text-sm font-semibold text-zinc-100">{task.title}</h3>
                          {task.description && (
                            <p className="text-sm text-zinc-400 mt-1 line-clamp-2 leading-relaxed">{task.description}</p>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-3 self-start sm:self-center ml-7 sm:ml-0">
                        <span className={`text-[10px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-md border ${statusColors[task.status] || ""}`}>
                          {task.status.replace("_", " ")}
                        </span>
                        <span className={`text-xs ${priorityColors[task.priority] || "text-zinc-500"}`}>
                          {task.priority.charAt(0).toUpperCase() + task.priority.slice(1)}
                        </span>
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </motion.div>
          ) : (
            /* Goals List */
            <motion.div 
              key="goals"
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -10 }}
              transition={{ duration: 0.2 }}
              className="grid grid-cols-1 md:grid-cols-2 gap-4"
            >
              {goalsLoading ? (
                // Loading Skeletons
                <>
                  <ListItemSkeleton />
                  <ListItemSkeleton />
                </>
              ) : goals && goals.length === 0 ? (
                <div className="col-span-full text-center py-16 glass rounded-2xl border-dashed border-zinc-800">
                  <div className="w-16 h-16 rounded-full bg-zinc-900 flex items-center justify-center mx-auto mb-4 shadow-inner">
                    <Target className="w-8 h-8 text-zinc-600" />
                  </div>
                  <p className="text-zinc-400 font-medium">No goals defined yet</p>
                  <p className="text-sm text-zinc-500 mt-1">
                    Goals help your Brain understand what you're working toward
                  </p>
                </div>
              ) : (
                goals?.map((goal: any, i: number) => (
                  <motion.div
                    key={goal.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.05, duration: 0.3 }}
                    className="glass card-hover border-zinc-800/50 rounded-2xl p-6"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-teal-500/10 border border-teal-500/20 flex items-center justify-center shrink-0">
                          <Target className="w-5 h-5 text-teal-400" />
                        </div>
                        <div>
                          <h3 className="text-base font-semibold text-zinc-100 line-clamp-1">{goal.title}</h3>
                          <span className="text-xs font-medium text-teal-400 capitalize">{goal.status}</span>
                        </div>
                      </div>
                    </div>
                    
                    {goal.description && (
                      <p className="text-sm text-zinc-400 leading-relaxed mb-6 line-clamp-2">{goal.description}</p>
                    )}
                    
                    {/* Progress bar */}
                    <div className="mt-auto">
                      <div className="flex items-center justify-between text-xs font-medium mb-2">
                        <span className="text-zinc-300">Progress</span>
                        <span className="text-white bg-zinc-800 px-2 py-0.5 rounded">{Math.round(goal.progress * 100)}%</span>
                      </div>
                      <div className="w-full bg-zinc-900 rounded-full h-2 border border-zinc-800 overflow-hidden">
                        <div
                          className="bg-gradient-to-r from-violet-500 to-teal-400 h-full rounded-full transition-all duration-1000 ease-out relative"
                          style={{ width: `${Math.round(goal.progress * 100)}%` }}
                        >
                          <div className="absolute inset-0 bg-white/20 shimmer" />
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
