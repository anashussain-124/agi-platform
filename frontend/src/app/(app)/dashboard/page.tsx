"use client";

import { Brain, Activity, Database, ListChecks, Zap, Cpu } from "lucide-react";
import { motion } from "framer-motion";

export default function DashboardPage() {
  const stats = [
    { title: "System Health", value: "Optimal", icon: Activity, color: "text-emerald-400", bg: "bg-emerald-400/10" },
    { title: "Active Tasks", value: "3", icon: ListChecks, color: "text-violet-400", bg: "bg-violet-400/10" },
    { title: "Memory Nodes", value: "1,204", icon: Database, color: "text-teal-400", bg: "bg-teal-400/10" },
    { title: "Brain Sync", value: "99.9%", icon: Brain, color: "text-blue-400", bg: "bg-blue-400/10" },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-end gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-white mb-1">Dashboard</h1>
          <p className="text-zinc-400 text-sm">Welcome back to your AGI Platform overview.</p>
        </div>
        <button className="flex items-center gap-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-sm px-4 py-2 rounded-lg transition-colors border border-zinc-700">
          <Zap className="w-4 h-4 text-violet-400" />
          <span>Quick Action</span>
        </button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1, duration: 0.5 }}
            className="p-5 rounded-2xl bg-zinc-900/50 border border-zinc-800/50 backdrop-blur-xl flex items-start gap-4 hover:border-zinc-700 transition-colors"
          >
            <div className={`p-3 rounded-xl ${stat.bg}`}>
              <stat.icon className={`w-5 h-5 ${stat.color}`} />
            </div>
            <div>
              <p className="text-sm text-zinc-400 font-medium">{stat.title}</p>
              <h3 className="text-2xl font-bold text-white mt-1">{stat.value}</h3>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        {/* Activity Feed */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4, duration: 0.5 }}
          className="lg:col-span-2 rounded-2xl bg-zinc-900/50 border border-zinc-800/50 backdrop-blur-xl p-6"
        >
          <div className="flex items-center gap-2 mb-6">
            <Activity className="w-5 h-5 text-violet-400" />
            <h2 className="text-lg font-semibold text-white">Recent Agent Activity</h2>
          </div>
          <div className="space-y-4">
            {[
              { time: "2 mins ago", text: "Learning engine extracted 3 new user preferences.", type: "memory" },
              { time: "15 mins ago", text: "Background task 'Optimize Database' completed.", type: "task" },
              { time: "1 hr ago", text: "Web search plugin successfully scraped target URL.", type: "plugin" },
            ].map((activity, i) => (
              <div key={i} className="flex gap-4 p-3 rounded-lg hover:bg-zinc-800/50 transition-colors">
                <div className="w-2 h-2 mt-2 rounded-full bg-violet-500 shrink-0" />
                <div>
                  <p className="text-zinc-200 text-sm">{activity.text}</p>
                  <span className="text-xs text-zinc-500">{activity.time}</span>
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
          className="rounded-2xl bg-zinc-900/50 border border-zinc-800/50 backdrop-blur-xl p-6 flex flex-col"
        >
          <div className="flex items-center gap-2 mb-6">
            <Cpu className="w-5 h-5 text-teal-400" />
            <h2 className="text-lg font-semibold text-white">System Load</h2>
          </div>
          
          <div className="flex-1 space-y-6">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-zinc-400">Celery Workers</span>
                <span className="text-white font-mono">45%</span>
              </div>
              <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-violet-500 to-violet-400 w-[45%]" />
              </div>
            </div>
            
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-zinc-400">Memory Allocation</span>
                <span className="text-white font-mono">72%</span>
              </div>
              <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                <div className="h-full bg-gradient-to-r from-teal-500 to-teal-400 w-[72%]" />
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
