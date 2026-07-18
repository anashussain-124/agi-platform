"use client";

import { Brain, Activity, Database, ListChecks, Zap, Cpu } from "lucide-react";
import { motion } from "framer-motion";

export default function DashboardPage() {
  const stats = [
    { title: "System Health", value: "Optimal", icon: Activity, color: "text-teal", dot: "bg-teal" },
    { title: "Active Tasks", value: "3", icon: ListChecks, color: "text-signal", dot: "bg-signal" },
    { title: "Memory Nodes", value: "1,204", icon: Database, color: "text-ion", dot: "bg-ion" },
    { title: "Brain Sync", value: "99.9%", icon: Brain, color: "text-emerald-400", dot: "bg-emerald-400" },
  ];

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-[var(--bone)] mb-2 flex items-center gap-3 font-display">
            Mission Control
            <span className="status-dot w-2 h-2 rounded-full bg-teal ml-1" />
          </h1>
          <p className="text-[var(--muted)] text-sm font-mono tracking-wide">Welcome back to your AGI Platform overview.</p>
        </div>
        <button className="flex items-center gap-2 bg-[var(--panel-2)] hover:bg-[var(--panel)] text-[var(--bone)] text-sm px-5 py-2.5 rounded-xl transition-all border border-[var(--hairline-strong)] hover:border-[var(--signal)] shadow-sm group">
          <Zap className="w-4 h-4 text-signal group-hover:scale-110 transition-transform" />
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
            transition={{ delay: i * 0.08, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            className="instrument ticks p-5 rounded-2xl flex items-start gap-4 group hover:border-[var(--hairline-strong)] transition-colors"
          >
            <div className={`p-3 rounded-xl border border-[var(--hairline-strong)] bg-[var(--panel-2)] ${stat.color}`}>
              <stat.icon className="w-5 h-5" />
            </div>
            <div className="z-10">
              <p className="text-xs text-[var(--muted)] font-mono uppercase tracking-widest mb-1">{stat.title}</p>
              <h3 className="text-2xl font-bold text-[var(--bone)] mt-1 tracking-tight font-display">{stat.value}</h3>
            </div>
            <span className={`ml-auto w-2 h-2 rounded-full ${stat.dot} status-dot`} />
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Activity Feed */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="lg:col-span-2 instrument p-6 flex flex-col h-[400px]"
        >
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-[var(--ion-dim)] rounded-lg border border-[var(--ion-dim)]">
                <Activity className="w-4 h-4 text-ion" />
              </div>
              <h2 className="text-lg font-semibold text-[var(--bone)] font-display">Recent Agent Activity</h2>
            </div>
            <button className="text-xs font-medium text-[var(--muted)] hover:text-[var(--bone)] transition-colors font-mono">
              VIEW ALL →
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
              <div key={i} className="flex gap-4 p-3 rounded-xl hover:bg-[var(--panel-2)] transition-colors group">
                <div className="w-2 h-2 mt-2 rounded-full bg-ion/50 group-hover:bg-signal transition-colors shrink-0 shadow-[0_0_8px_rgba(255,179,71,0.4)]" />
                <div>
                  <p className="text-[var(--bone-soft)] text-sm leading-relaxed">{activity.text}</p>
                  <span className="text-xs text-[var(--muted)] font-medium mt-1 block font-mono">{activity.time}</span>
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
          className="instrument p-6 flex flex-col h-[400px]"
        >
          <div className="flex items-center gap-3 mb-8">
            <div className="p-2 bg-[var(--teal-dim)] rounded-lg border border-[var(--teal-dim)]">
              <Cpu className="w-4 h-4 text-teal" />
            </div>
            <h2 className="text-lg font-semibold text-[var(--bone)] font-display">System Load</h2>
          </div>

          <div className="flex-1 space-y-8">
            <div>
              <div className="flex justify-between text-sm mb-3">
                <span className="text-[var(--bone-soft)] font-medium flex items-center gap-2 font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-signal" />
                  Celery Workers
                </span>
                <span className="text-[var(--bone)] font-mono bg-[var(--panel-2)] px-2 py-0.5 rounded text-xs">45%</span>
              </div>
              <div className="h-2 bg-[var(--ink)] rounded-full overflow-hidden border border-[var(--hairline)]">
                <div className="h-full bg-[var(--gradient-primary)] w-[45%] relative">
                  <div className="absolute inset-0 bg-white/20 shimmer" />
                </div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-sm mb-3">
                <span className="text-[var(--bone-soft)] font-medium flex items-center gap-2 font-mono">
                  <span className="w-1.5 h-1.5 rounded-full bg-teal" />
                  Memory Allocation
                </span>
                <span className="text-[var(--bone)] font-mono bg-[var(--panel-2)] px-2 py-0.5 rounded text-xs">72%</span>
              </div>
              <div className="h-2 bg-[var(--ink)] rounded-full overflow-hidden border border-[var(--hairline)]">
                <div className="h-full bg-gradient-to-r from-teal to-emerald-400 w-[72%] relative">
                  <div className="absolute inset-0 bg-white/20 shimmer" />
                </div>
              </div>
            </div>

            <div className="mt-auto pt-6 border-t border-[var(--hairline)]">
               <div className="flex items-center justify-between p-3 rounded-xl bg-[var(--panel-2)] border border-[var(--hairline)]">
                 <div className="flex items-center gap-3">
                   <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                   <span className="text-sm font-medium text-[var(--bone-soft)]">Database Node</span>
                 </div>
                 <span className="text-xs text-emerald-400 font-medium font-mono">Connected</span>
               </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
