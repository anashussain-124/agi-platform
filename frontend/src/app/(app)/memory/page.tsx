"use client";

import { useState, useEffect } from "react";
import {
  Database,
  Search,
  Plus,
  BookOpen,
  Brain,
  Tag,
  Clock,
  TrendingUp,
  Archive,
} from "lucide-react";
import { api } from "@/lib/api";

const memoryTypes = [
  { value: "", label: "All Memories", icon: Database },
  { value: "working", label: "Working", icon: Brain },
  { value: "episodic", label: "Episodic", icon: Clock },
  { value: "semantic", label: "Semantic", icon: BookOpen },
  { value: "procedural", label: "Procedural", icon: TrendingUp },
  { value: "knowledge", label: "Knowledge", icon: Archive },
];

export default function MemoryPage() {
  const [memories, setMemories] = useState<any[]>([]);
  const [filter, setFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [showStore, setShowStore] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newType, setNewType] = useState("semantic");

  useEffect(() => {
    loadMemories();
  }, [filter]);

  const loadMemories = async () => {
    try {
      const data = await api.getMemories(filter || undefined);
      setMemories(data);
    } catch {
      setMemories([]);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadMemories();
      return;
    }
    try {
      const results = await api.searchMemories(searchQuery);
      setMemories(results);
    } catch {
      // fallback
    }
  };

  const handleStore = async () => {
    if (!newTitle.trim() || !newContent.trim()) return;
    try {
      await api.storeMemory({
        memory_type: newType,
        title: newTitle,
        content: newContent,
      });
      setShowStore(false);
      setNewTitle("");
      setNewContent("");
      loadMemories();
    } catch {
      // handle error
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-100">Memory</h1>
          <p className="text-sm text-zinc-500 mt-1">
            Your Brain's persistent knowledge store
          </p>
        </div>
        <button
          onClick={() => setShowStore(!showStore)}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-violet-600 hover:bg-violet-500 text-white text-xs font-medium rounded-lg transition-colors"
        >
          <Plus className="w-3.5 h-3.5" />
          Store Memory
        </button>
      </div>

      {/* Store memory form */}
      {showStore && (
        <div className="bg-zinc-900/80 border border-zinc-800 rounded-xl p-4 space-y-3">
          <input
            type="text"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="Memory title..."
            className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500/50"
          />
          <textarea
            value={newContent}
            onChange={(e) => setNewContent(e.target.value)}
            placeholder="What do you want to remember?"
            rows={4}
            className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500/50 resize-none"
          />
          <div className="flex items-center gap-2">
            <select
              value={newType}
              onChange={(e) => setNewType(e.target.value)}
              className="bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-1.5 text-xs text-zinc-300 focus:outline-none"
            >
              <option value="semantic">Semantic (facts/knowledge)</option>
              <option value="working">Working (current context)</option>
              <option value="episodic">Episodic (experiences)</option>
              <option value="procedural">Procedural (how-to)</option>
              <option value="knowledge">Knowledge (documents)</option>
            </select>
            <button
              onClick={handleStore}
              className="px-3 py-1.5 bg-teal-600 hover:bg-teal-500 text-white text-xs font-medium rounded-lg transition-colors"
            >
              Save
            </button>
          </div>
        </div>
      )}

      {/* Search and filter */}
      <div className="flex items-center gap-3">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Search memories..."
            className="w-full bg-zinc-900 border border-zinc-800 rounded-lg pl-10 pr-3 py-2 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500/50"
          />
        </div>
        <div className="flex gap-1">
          {memoryTypes.map((type) => {
            const Icon = type.icon;
            const isActive = filter === type.value;
            return (
              <button
                key={type.value}
                onClick={() => setFilter(type.value)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-colors ${
                  isActive
                    ? "bg-violet-500/10 text-violet-400 border border-violet-500/20"
                    : "text-zinc-500 hover:text-zinc-300 hover:bg-zinc-800/50"
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span className="hidden md:inline">{type.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Memory list */}
      <div className="space-y-2">
        {memories.length === 0 ? (
          <div className="text-center py-12">
            <Database className="w-8 h-8 text-zinc-700 mx-auto mb-3" />
            <p className="text-sm text-zinc-500">No memories stored yet</p>
            <button
              onClick={() => setShowStore(true)}
              className="text-xs text-violet-400 hover:text-violet-300 mt-2"
            >
              Store your first memory
            </button>
          </div>
        ) : (
          memories.map((mem) => (
            <div
              key={mem.id}
              className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-4 hover:border-zinc-700 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-md bg-violet-500/10 flex items-center justify-center">
                    <Database className="w-3.5 h-3.5 text-violet-400" />
                  </div>
                  <div>
                    <h3 className="text-sm font-medium text-zinc-200">{mem.title}</h3>
                    <p className="text-xs text-zinc-500 mt-0.5">{mem.summary}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] uppercase text-zinc-600 bg-zinc-800 px-2 py-0.5 rounded-full">
                    {mem.memory_type}
                  </span>
                  <span className="text-[10px] text-zinc-600">
                    {new Date(mem.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
