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
} from "lucide-react";
import { api } from "@/lib/api";

const statusColors: Record<string, string> = {
  pending: "bg-zinc-800 text-zinc-400",
  in_progress: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  completed: "bg-teal-500/10 text-teal-400 border-teal-500/20",
  failed: "bg-red-500/10 text-red-400 border-red-500/20",
  cancelled: "bg-zinc-800 text-zinc-500",
  approval_needed: "bg-amber-500/10 text-amber-400 border-amber-500/20",
};

const priorityColors: Record<string, string> = {
  low: "text-zinc-500",
  medium: "text-amber-400",
  high: "text-red-400",
  critical: "text-red-500",
};

export default function TasksPage() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [goals, setGoals] = useState<any[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newTask, setNewTask] = useState({ title: "", description: "", priority: "medium" });
  const [tab, setTab] = useState<"tasks" | "goals">("tasks");

  useEffect(() => {
    loadTasks();
    loadGoals();
  }, []);

  const loadTasks = async () => {
    try {
      const data = await api.getTasks();
      setTasks(data);
    } catch {
      setTasks([]);
    }
  };

  const loadGoals = async () => {
    try {
      const data = await api.getGoals();
      setGoals(data);
    } catch {
      setGoals([]);
    }
  };

  const handleCreate = async () => {
    if (!newTask.title.trim()) return;
    try {
      await api.createTask(newTask);
      setShowCreate(false);
      setNewTask({ title: "", description: "", priority: "medium" });
      loadTasks();
    } catch {
      // handle error
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Tasks & Goals</h1>
          <p className="text-sm text-zinc-500 mt-1">
            Plan, execute, and track progress with your Brain
          </p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-violet-600 hover:bg-violet-500 text-white text-xs font-medium rounded-lg transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          New Task
        </button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-zinc-900 border border-zinc-800 rounded-lg p-1 w-fit">
        <button
          onClick={() => setTab("tasks")}
          className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${
            tab === "tasks" ? "bg-zinc-800 text-zinc-200" : "text-zinc-500 hover:text-zinc-300"
          }`}
        >
          <ListChecks className="w-3.5 h-3.5 inline mr-1.5" />
          Tasks
        </button>
        <button
          onClick={() => setTab("goals")}
          className={`px-4 py-1.5 rounded-md text-xs font-medium transition-colors ${
            tab === "goals" ? "bg-zinc-800 text-zinc-200" : "text-zinc-500 hover:text-zinc-300"
          }`}
        >
          <Target className="w-3.5 h-3.5 inline mr-1.5" />
          Goals
        </button>
      </div>

      {/* Create task form */}
      {showCreate && (
        <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4 space-y-3">
          <input
            type="text"
            value={newTask.title}
            onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
            placeholder="Task title..."
            className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500/50"
          />
          <textarea
            value={newTask.description}
            onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
            placeholder="What needs to be done?"
            rows={3}
            className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500/50 resize-none"
          />
          <div className="flex items-center gap-2">
            <select
              value={newTask.priority}
              onChange={(e) => setNewTask({ ...newTask, priority: e.target.value })}
              className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1.5 text-xs text-zinc-300 focus:outline-none"
            >
              <option value="low">Low Priority</option>
              <option value="medium">Medium Priority</option>
              <option value="high">High Priority</option>
              <option value="critical">Critical</option>
            </select>
            <button
              onClick={handleCreate}
              className="px-3 py-1.5 bg-teal-600 hover:bg-teal-500 text-white text-xs font-medium rounded-lg transition-colors"
            >
              Create
            </button>
          </div>
        </div>
      )}

      {tab === "tasks" ? (
        /* Tasks List */
        <div className="space-y-2">
          {tasks.length === 0 ? (
            <div className="text-center py-12">
              <ListChecks className="w-8 h-8 text-zinc-700 mx-auto mb-3" />
              <p className="text-sm text-zinc-500">No tasks yet</p>
              <button
                onClick={() => setShowCreate(true)}
                className="text-xs text-violet-400 hover:text-violet-300 mt-2"
              >
                Create your first task
              </button>
            </div>
          ) : (
            tasks.map((task) => (
              <div
                key={task.id}
                className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 hover:border-zinc-700 transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-2 h-2 rounded-full ${
                        task.status === "completed"
                          ? "bg-teal-500"
                          : task.status === "in_progress"
                          ? "bg-blue-500"
                          : task.status === "failed"
                          ? "bg-red-500"
                          : "bg-zinc-600"
                      }`}
                    />
                    <div>
                      <h3 className="text-sm font-medium text-zinc-200">{task.title}</h3>
                      {task.description && (
                        <p className="text-xs text-zinc-500 mt-0.5">{task.description}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] uppercase px-2 py-0.5 rounded-full border ${statusColors[task.status] || ""}`}>
                      {task.status.replace("_", " ")}
                    </span>
                    <span className={`text-[10px] ${priorityColors[task.priority] || "text-zinc-500"}`}>
                      {task.priority}
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      ) : (
        /* Goals List */
        <div className="space-y-3">
          {goals.length === 0 ? (
            <div className="text-center py-12">
              <Target className="w-8 h-8 text-zinc-700 mx-auto mb-3" />
              <p className="text-sm text-zinc-500">No goals defined yet</p>
              <p className="text-xs text-zinc-600 mt-1">
                Goals help your Brain understand what you're working toward
              </p>
            </div>
          ) : (
            goals.map((goal) => (
              <div
                key={goal.id}
                className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-sm font-medium text-zinc-200">{goal.title}</h3>
                    {goal.description && (
                      <p className="text-xs text-zinc-500 mt-0.5">{goal.description}</p>
                    )}
                  </div>
                  <span className="text-xs text-zinc-500 capitalize">{goal.status}</span>
                </div>
                {/* Progress bar */}
                <div className="w-full bg-zinc-800 rounded-full h-1.5">
                  <div
                    className="bg-gradient-to-r from-violet-500 to-teal-500 h-1.5 rounded-full transition-all"
                    style={{ width: `${Math.round(goal.progress * 100)}%` }}
                  />
                </div>
                <p className="text-xs text-zinc-500 mt-1">
                  {Math.round(goal.progress * 100)}% complete
                </p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}
