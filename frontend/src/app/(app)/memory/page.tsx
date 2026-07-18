"use client";

import { useState, useEffect } from "react";
import {
  Database,
  Search,
  Plus,
  BookOpen,
  Brain,
  Clock,
  TrendingUp,
  Archive,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import { useApi } from "@/hooks/use-api";
import { ListItemSkeleton } from "@/components/ui/skeleton";
import { showToast } from "@/components/ui/toast";

const memoryTypes = [
  { value: "", label: "All Memories", icon: Database },
  { value: "working", label: "Working", icon: Brain },
  { value: "episodic", label: "Episodic", icon: Clock },
  { value: "semantic", label: "Semantic", icon: BookOpen },
  { value: "procedural", label: "Procedural", icon: TrendingUp },
  { value: "knowledge", label: "Knowledge", icon: Archive },
];

export default function MemoryPage() {
  const [filter, setFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [showStore, setShowStore] = useState(false);
  
  // Store form state
  const [newTitle, setNewTitle] = useState("");
  const [newContent, setNewContent] = useState("");
  const [newType, setNewType] = useState("semantic");
  const [isStoring, setIsStoring] = useState(false);

  // Fetch memories using the new custom hook
  const { 
    data: memories = [], 
    loading, 
    refetch: fetchMemories 
  } = useApi({
    fetcher: async () => {
      if (searchQuery.trim()) {
        const results = await api.searchMemories(searchQuery);
        return results.map(r => ({
          id: r.id,
          title: r.title,
          memory_type: r.memory_type,
          summary: r.content,
          created_at: new Date().toISOString()
        }));
      }
      return api.getMemories(filter || undefined);
    },
    errorMessage: "Failed to load memories",
  });

  // Re-fetch when filter changes
  useEffect(() => {
    fetchMemories();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [filter]);

  const handleSearch = () => {
    fetchMemories();
  };

  const handleStore = async () => {
    if (!newTitle.trim() || !newContent.trim()) {
      showToast("Please fill in both title and content", "error");
      return;
    }
    
    setIsStoring(true);
    try {
      await api.storeMemory({
        memory_type: newType,
        title: newTitle,
        content: newContent,
      });
      showToast("Memory stored successfully", "success");
      setShowStore(false);
      setNewTitle("");
      setNewContent("");
      fetchMemories();
    } catch (err: any) {
      showToast(err.message || "Failed to store memory", "error");
    } finally {
      setIsStoring(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight flex items-center gap-3">
            Memory Bank
            <div className="status-pulse w-2 h-2 rounded-full bg-violet-400 ml-2" />
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Your Brain's persistent knowledge store
          </p>
        </div>
        <button
          onClick={() => setShowStore(!showStore)}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-medium text-sm transition-all shadow-sm
            ${showStore 
              ? "bg-zinc-800 text-zinc-300 hover:bg-zinc-700" 
              : "bg-[var(--gradient-primary)] text-zinc-950 hover:opacity-90 shadow-[var(--shadow-glow)]"
            }`}
        >
          <Plus className={`w-4 h-4 transition-transform ${showStore ? "rotate-45" : ""}`} />
          {showStore ? "Cancel" : "Store Memory"}
        </button>
      </div>

      {/* Store memory form */}
      <AnimatePresence>
        {showStore && (
          <motion.div
            initial={{ opacity: 0, height: 0, y: -20 }}
            animate={{ opacity: 1, height: "auto", y: 0 }}
            exit={{ opacity: 0, height: 0, y: -20 }}
            className="overflow-hidden"
          >
            <div className="glass-strong border-zinc-800/50 rounded-2xl p-5 space-y-4 shadow-lg mb-6">
              <input
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="Memory title..."
                className="w-full bg-zinc-900/50 border border-zinc-800/80 rounded-xl px-4 py-3 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-violet-500 transition-all"
                disabled={isStoring}
              />
              <textarea
                value={newContent}
                onChange={(e) => setNewContent(e.target.value)}
                placeholder="What do you want the agent to remember?"
                rows={4}
                className="w-full bg-zinc-900/50 border border-zinc-800/80 rounded-xl px-4 py-3 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-violet-500 transition-all resize-none custom-scrollbar"
                disabled={isStoring}
              />
              <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
                <div className="flex items-center gap-3">
                  <span className="text-xs font-medium text-zinc-500 uppercase tracking-wider">Type:</span>
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value)}
                    className="bg-zinc-900 border border-zinc-800 rounded-lg px-3 py-2 text-sm text-zinc-300 focus:outline-none focus:ring-1 focus:ring-violet-500"
                    disabled={isStoring}
                  >
                    <option value="semantic">Semantic (facts/knowledge)</option>
                    <option value="working">Working (current context)</option>
                    <option value="episodic">Episodic (experiences)</option>
                    <option value="procedural">Procedural (how-to)</option>
                    <option value="knowledge">Knowledge (documents)</option>
                  </select>
                </div>
                <button
                  onClick={handleStore}
                  disabled={isStoring}
                  className="px-6 py-2 bg-teal-500 hover:bg-teal-400 text-zinc-950 text-sm font-semibold rounded-xl transition-all shadow-[0_0_15px_rgba(45,212,191,0.2)] disabled:opacity-50"
                >
                  {isStoring ? "Saving..." : "Save Memory"}
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Search and filter */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center gap-4">
        <div className="flex-1 relative group">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500 group-focus-within:text-violet-400 transition-colors" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Search memories..."
            className="w-full bg-zinc-900/80 border border-zinc-800/80 rounded-xl pl-10 pr-3 py-2.5 text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none focus:ring-1 focus:ring-violet-500 transition-all glass"
          />
        </div>
        <div className="flex flex-wrap gap-2 overflow-x-auto custom-scrollbar pb-2 md:pb-0">
          {memoryTypes.map((type) => {
            const Icon = type.icon;
            const isActive = filter === type.value;
            return (
              <button
                key={type.value}
                onClick={() => setFilter(type.value)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-medium transition-all whitespace-nowrap
                  ${isActive
                    ? "bg-violet-500/15 text-violet-300 border border-violet-500/30 shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)]"
                    : "bg-zinc-900/50 text-zinc-400 border border-zinc-800/50 hover:text-zinc-200 hover:bg-zinc-800 hover:border-zinc-700 glass"
                  }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? "text-violet-400" : ""}`} />
                <span>{type.label}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Memory list */}
      <div className="space-y-3">
        {loading ? (
          // Loading Skeletons
          <>
            <ListItemSkeleton />
            <ListItemSkeleton />
            <ListItemSkeleton />
            <ListItemSkeleton />
          </>
        ) : memories && memories.length === 0 ? (
          // Empty State
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-16 glass rounded-2xl border-dashed border-zinc-800"
          >
            <div className="w-16 h-16 rounded-full bg-zinc-900 flex items-center justify-center mx-auto mb-4 shadow-inner">
              <Database className="w-8 h-8 text-zinc-600" />
            </div>
            <p className="text-zinc-400 font-medium">No memories found</p>
            <button
              onClick={() => setShowStore(true)}
              className="text-sm text-violet-400 hover:text-violet-300 mt-2 font-medium transition-colors"
            >
              Store your first memory
            </button>
          </motion.div>
        ) : (
          // Data List
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {memories?.map((mem: any, i: number) => (
              <motion.div
                key={mem.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05, duration: 0.3 }}
                className="glass card-hover border-zinc-800/50 rounded-2xl p-5 flex flex-col h-full"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center shrink-0">
                      {/* Dynamically choose icon based on type if possible, fallback to Database */}
                      <Database className="w-4 h-4 text-violet-400" />
                    </div>
                    <h3 className="text-sm font-semibold text-zinc-100 line-clamp-1">{mem.title}</h3>
                  </div>
                </div>
                
                <p className="text-sm text-zinc-400 leading-relaxed mb-6 flex-1 line-clamp-3">
                  {mem.summary || mem.content}
                </p>
                
                <div className="flex items-center justify-between mt-auto pt-4 border-t border-zinc-800/50">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-violet-400 bg-violet-500/10 border border-violet-500/20 px-2.5 py-1 rounded-md">
                    {mem.memory_type}
                  </span>
                  <span className="text-xs font-medium text-zinc-500 flex items-center gap-1.5">
                    <Clock className="w-3 h-3" />
                    {new Date(mem.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                  </span>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
