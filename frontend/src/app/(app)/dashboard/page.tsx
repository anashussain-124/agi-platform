"use client";

import { Brain, Activity, Database, ListChecks, Zap, Cpu } from "lucide-react";
import { motion } from "framer-motion";

export default function DashboardPage() {
  const stats = [
    { title: "System Health", value: "Optimal", icon: Activity, color: "text-teal-400", bg: "bg-teal-500/10", border: "border-teal-500/20" },
    { title: "Active Tasks", value: "3", icon: ListChecks, color: "text-violet-400", bg: "bg-violet-500/10", border: "border-violet-500/20" },
    { title: "Memory Nodes", value: "1,204", icon: Database, color: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/20" },
    { title: "Brain Sync", value: "99.9%", icon: Brain, color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4 animate-fade-in">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-2 flex items-center gap-3">
            Dashboard
            <div className="status-pulse w-2 h-2 rounded-full bg-teal-400 ml-2" />
          </h1>
          <p className="text-zinc-400 text-sm">Welcome back to your AGI Platform overview.</p>
        </div>
        <button className="flex items-center gap-2 bg-zinc-900 hover:bg-zinc-800 text-zinc-100 text-sm px-5 py-2.5 rounded-xl transition-all border border-zinc-700/50 hover:border-zinc-600 shadow-sm hover:shadow-md group">
          <Zap className="w-4 h-4 text-violet-400 group-hover:scale-110 transition-transform" />
          <span className="font-medium">Quick Action</span>
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1, duration: 0.5, ease: "easeOut" }}
            className="glass card-hover p-5 rounded-2xl flex items-start gap-4 card-gradient"
          >
            <div className={`p-3 rounded-xl border ${stat.bg} ${stat.border}`}>
              <stat.icon className={`w-5 h-5 ${stat.color}`} />
            </div>
            <div className="z-10">
              <p className="text-sm text-zinc-400 font-medium">{stat.title}</p>
              <h3 className="text-2xl font-bold text-white mt-1 tracking-tight">{stat.value}</h3>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity Feed */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="lg:col-span-2 rounded-2xl glass p-6 flex flex-col h-[400px]"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-violet-500/10 rounded-lg border border-violet-500/20">
                <Activity className="w-4 h-4 text-violet-400" />
              </div>
              <h2 className="text-lg font-semibold text-white">Recent Agent Activity</h2>
            </div>
            <button className="text-xs font-medium text-zinc-400 hover:text-zinc-200 transition-colors">
              View All
            </button>
          </div>
          <div className="space-y-4 overflow-y-auto pr-2 custom-scrollbar flex-1">
            {[
              { time: "2 mins ago", text: "Learning engine extracted 3 new user preferences.", type: "memory" },
              { time: "15 mins ago", text: "Background task 'Optimize Database' completed.", type: "task" },
              { time: "1 hr ago", text: "Web search plugin successfully scraped target URL.", type: "plugin" },
              { time: "2 hrs ago", text: "Security agent completed code scan (no issues).", type: "security" },
              { time: "3 hrs ago", text: "New conversation initiated in 'Project Planning'.", type: "chat" },
            ].map((activity, i) => (
              <div key={i} className="flex gap-4 p-3 rounded-xl hover:bg-zinc-800/40 transition-colors group">
                <div className="w-2 h-2 mt-2 rounded-full bg-violet-500/50 group-hover:bg-violet-400 transition-colors shrink-0 shadow-[0_0_8px_rgba(167,139,250,0.5)]" />
                <div>
                  <p className="text-zinc-200 text-sm leading-relaxed">{activity.text}</p>
                  <span className="text-xs text-zinc-500 font-medium mt-1 block">{activity.time}</span>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* System Load */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5, duration: 0.5 }}
          className="rounded-2xl glass p-6 flex flex-col h-[400px]"
        >
          <div className="flex items-center gap-3 mb-8">
            <div className="p-2 bg-teal-500/10 rounded-lg border border-teal-500/20">
              <Cpu className="w-4 h-4 text-teal-400" />
            </div>
            <h2 className="text-lg font-semibold text-white">System Load</h2>
          </div>
          
          <div className="flex-1 space-y-8">
            <div>
              <div className="flex justify-between text-sm mb-3">
                <span className="text-zinc-300 font-medium flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-violet-400" />
                  Celery Workers
                </span>
                <span className="text-white font-mono bg-zinc-800 px-2 py-0.5 rounded text-xs">45%</span>
              </div>
              <div className="h-2 bg-zinc-900 rounded-full overflow-hidden border border-zinc-800">
                <div className="h-full bg-[var(--gradient-primary)] w-[45%] relative">
                  <div className="absolute inset-0 bg-white/20 shimmer" />
                </div>
              </div>
            </div>
            
            <div>
              <div className="flex justify-between text-sm mb-3">
                <span className="text-zinc-300 font-medium flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-teal-400" />
                  Memory Allocation
                </span>
                <span className="text-white font-mono bg-zinc-800 px-2 py-0.5 rounded text-xs">72%</span>
              </div>
              <div className="h-2 bg-zinc-900 rounded-full overflow-hidden border border-zinc-800">
                <div className="h-full bg-gradient-to-r from-teal-500 to-emerald-400 w-[72%] relative">
                  <div className="absolute inset-0 bg-white/20 shimmer" />
                </div>
              </div>
            </div>
            
            <div className="mt-auto pt-6 border-t border-zinc-800/50">
               <div className="flex items-center justify-between p-3 rounded-xl bg-zinc-900/50 border border-zinc-800/50">
                 <div className="flex items-center gap-3">
                   <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                   <span className="text-sm font-medium text-zinc-300">Database Node</span>
                 </div>
                 <span className="text-xs text-emerald-400 font-medium">Connected</span>
               </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
