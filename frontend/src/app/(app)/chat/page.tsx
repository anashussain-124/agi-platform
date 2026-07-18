"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Brain, User, Loader2, Paperclip, MoreVertical, LayoutPanelLeft } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import { showToast } from "@/components/ui/toast";

interface Message {
  id: string;
  role: "user" | "ai";
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "placeholder",
      role: "ai",
      content: "Hello! I am your AGI Assistant. I can browse the web, read your files, and execute complex background tasks. What are we working on today?",
    }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Load the most recent conversation on mount
  useEffect(() => {
    async function loadLatestConversation() {
      try {
        const convs = await api.getConversations(1);
        if (convs && convs.length > 0) {
          setConversationId(convs[0].id);
        } else {
          setLoadingHistory(false);
        }
      } catch (err) {
        console.error("Failed to load conversation list:", err);
        setLoadingHistory(false);
      }
    }
    loadLatestConversation();
  }, []);

  // Fetch messages when conversationId is set
  useEffect(() => {
    if (!conversationId) return;
    const activeId = conversationId;

    async function loadMessages() {
      setLoadingHistory(true);
      try {
        const history = await api.getMessages(activeId);
        if (history && history.length > 0) {
          setMessages(
            history.map((msg) => ({
              id: msg.id,
              role: msg.role === "assistant" ? "ai" : "user",
              content: msg.content,
            }))
          );
        }
      } catch (err: any) {
        showToast("Failed to load chat history", "error");
      } finally {
        setLoadingHistory(false);
      }
    }
    loadMessages();
  }, [conversationId]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMessage = input;
    const newMsg: Message = { id: Date.now().toString(), role: "user", content: userMessage };
    
    // Clear placeholder message if it's the only one
    setMessages(prev => 
      prev.length === 1 && prev[0].id === "placeholder" ? [newMsg] : [...prev, newMsg]
    );
    setInput("");
    setIsTyping(true);

    try {
      const data = await api.chat(userMessage, conversationId || undefined);
      
      // Save conversation ID if this was a new conversation
      if (!conversationId && data.conversation_id) {
        setConversationId(data.conversation_id);
      }

      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "ai",
          content: data.response || "No response received.",
        }
      ]);
    } catch (err: any) {
      showToast(err.message || "Failed to connect to Brain API", "error");
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: "ai",
          content: "Error connecting to Brain API: " + err.message,
        }
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-6rem)] gap-6 animate-fade-in">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col glass-strong rounded-3xl border border-zinc-800/50 shadow-2xl overflow-hidden relative">
        {/* Chat Header */}
        <div className="flex justify-between items-center px-6 py-4 border-b border-zinc-800/50 bg-zinc-900/40 backdrop-blur-xl z-10">
          <div className="flex items-center gap-4">
            <div className="w-11 h-11 rounded-2xl bg-[var(--gradient-primary)] p-[1px] shadow-[var(--shadow-glow)] shrink-0">
              <div className="w-full h-full bg-zinc-950 rounded-[15px] flex items-center justify-center">
                <Brain className="w-5 h-5 text-violet-400 brain-glow" />
              </div>
            </div>
            <div>
              <h2 className="text-zinc-100 font-semibold tracking-tight">AGI Orchestrator</h2>
              <p className="text-xs font-medium text-emerald-400 flex items-center gap-1.5 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 status-pulse" />
                Online & Ready
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button className="p-2.5 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50 rounded-xl transition-all">
              <LayoutPanelLeft className="w-5 h-5" />
            </button>
            <button className="p-2.5 text-zinc-400 hover:text-zinc-100 hover:bg-zinc-800/50 rounded-xl transition-all">
              <MoreVertical className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gradient-to-b from-transparent to-zinc-900/20 custom-scrollbar relative z-0">
          {loadingHistory && conversationId ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
            </div>
          ) : (
            <AnimatePresence initial={false}>
              {messages.map((msg) => (
                <motion.div
                  initial={{ opacity: 0, y: 10, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  key={msg.id}
                  className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
                >
                  <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 shadow-sm ${
                    msg.role === "user" 
                      ? "bg-zinc-800 border border-zinc-700 text-zinc-300" 
                      : "bg-[var(--gradient-primary)] text-zinc-950 shadow-[var(--shadow-glow)]"
                  }`}>
                    {msg.role === "user" ? <User className="w-5 h-5" /> : <Brain className="w-5 h-5" />}
                  </div>
                  
                  <div className={`max-w-[80%] rounded-2xl px-5 py-3.5 shadow-sm ${
                    msg.role === "user" 
                      ? "bg-violet-600/90 text-white rounded-tr-sm border border-violet-500/30 backdrop-blur-md" 
                      : "bg-zinc-900/80 text-zinc-200 border border-zinc-700/50 rounded-tl-sm backdrop-blur-md"
                  }`}>
                    <p className="leading-relaxed whitespace-pre-wrap text-sm">{msg.content}</p>
                  </div>
                </motion.div>
              ))}

              {isTyping && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }} 
                  animate={{ opacity: 1, y: 0 }} 
                  exit={{ opacity: 0, scale: 0.9 }}
                  className="flex gap-4"
                >
                  <div className="w-9 h-9 rounded-xl bg-[var(--gradient-primary)] flex items-center justify-center shrink-0 shadow-[var(--shadow-glow)]">
                    <Brain className="w-5 h-5 text-zinc-950" />
                  </div>
                  <div className="bg-zinc-900/80 border border-zinc-700/50 rounded-2xl rounded-tl-sm px-5 py-4 flex items-center gap-1.5 backdrop-blur-md">
                    <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                    <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                    <span className="w-2 h-2 bg-violet-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          )}
          <div ref={messagesEndRef} className="h-1" />
        </div>

        {/* Input Area */}
        <div className="p-5 bg-zinc-900/40 backdrop-blur-xl border-t border-zinc-800/50 z-10">
          <form onSubmit={handleSend} className="relative flex items-center">
            <button type="button" className="absolute left-4 p-2 text-zinc-400 hover:text-violet-400 transition-colors group">
              <Paperclip className="w-5 h-5 group-hover:scale-110 transition-transform" />
            </button>
            
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Give the AGI a goal or ask a question..."
              className="w-full bg-zinc-900/80 border border-zinc-700/80 text-white rounded-2xl py-4 pl-14 pr-16 focus:outline-none focus:ring-1 focus:ring-violet-500 transition-all placeholder:text-zinc-500 glass shadow-inner"
              disabled={isTyping}
            />
            
            <button 
              type="submit" 
              disabled={!input.trim() || isTyping}
              className="absolute right-3 p-2.5 bg-[var(--gradient-primary)] hover:opacity-90 disabled:opacity-50 disabled:grayscale disabled:cursor-not-allowed text-zinc-950 rounded-xl transition-all flex items-center justify-center shadow-[var(--shadow-glow)]"
            >
              {isTyping ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-4 h-4 ml-0.5" />}
            </button>
          </form>
          <p className="text-center text-xs font-medium text-zinc-600 mt-4">
            The AGI may take time to execute complex goals. Background tasks can be monitored in the Dashboard.
          </p>
        </div>
      </div>
    </div>
  );
}
