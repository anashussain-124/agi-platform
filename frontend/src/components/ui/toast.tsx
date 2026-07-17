"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, CheckCircle2, AlertCircle, Info } from "lucide-react";

type ToastType = "success" | "error" | "info";

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

let addToastFn: ((message: string, type?: ToastType) => void) | null = null;

/** Call this from anywhere to show a toast. */
export function showToast(message: string, type: ToastType = "info") {
  addToastFn?.(message, type);
}

const toastConfig: Record<ToastType, { icon: typeof Info; bg: string; border: string; text: string }> = {
  success: { icon: CheckCircle2, bg: "bg-teal-500/10", border: "border-teal-500/30", text: "text-teal-400" },
  error: { icon: AlertCircle, bg: "bg-red-500/10", border: "border-red-500/30", text: "text-red-400" },
  info: { icon: Info, bg: "bg-violet-500/10", border: "border-violet-500/30", text: "text-violet-400" },
};

export function ToastProvider() {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const timers = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map());

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
  }, []);

  const addToast = useCallback((message: string, type: ToastType = "info") => {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 6)}`;
    setToasts(prev => [...prev.slice(-4), { id, message, type }]);
    const timer = setTimeout(() => removeToast(id), 4000);
    timers.current.set(id, timer);
  }, [removeToast]);

  useEffect(() => {
    addToastFn = addToast;
    return () => { addToastFn = null; };
  }, [addToast]);

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 max-w-sm">
      <AnimatePresence mode="popLayout">
        {toasts.map(toast => {
          const cfg = toastConfig[toast.type];
          const Icon = cfg.icon;
          return (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -10, scale: 0.95 }}
              transition={{ duration: 0.2 }}
              className={`flex items-start gap-3 px-4 py-3 rounded-xl border glass-strong shadow-lg ${cfg.bg} ${cfg.border}`}
            >
              <Icon className={`w-5 h-5 shrink-0 mt-0.5 ${cfg.text}`} />
              <p className="text-sm text-zinc-200 flex-1">{toast.message}</p>
              <button
                onClick={() => removeToast(toast.id)}
                className="text-zinc-500 hover:text-zinc-300 transition-colors shrink-0"
              >
                <X className="w-4 h-4" />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
