"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Brain, User, Loader2, Paperclip, MoreVertical } from "lucide-react";
import { motion } from "framer-motion";

interface Message {
  id: string;
  role: "user" | "ai";
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "1",
      role: "ai",
      content: "Hello! I am your AGI Assistant. I can browse the web, read your files, and execute complex background tasks. What are we working on today?",
    }
  ]);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;

    const newMsg: Message = { id: Date.now().toString(), role: "user", content: input };
    setMessages(prev => [...prev, newMsg]);
    setInput("");
    setIsTyping(true);

    // Call real API
    const token = localStorage.getItem("brain_token");
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    
    fetch(`${apiUrl}/api/brain/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`,
        "Bypass-Tunnel-Reminder": "true"
      },
      body: JSON.stringify({ message: input })
    })
      .then(res => res.json())
      .then(data => {
        setMessages(prev => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            role: "ai",
            content: data.response || "No response received.",
          }
        ]);
      })
      .catch(err => {
        setMessages(prev => [
          ...prev,
          {
            id: (Date.now() + 1).toString(),
            role: "ai",
            content: "Error connecting to Brain API: " + err.message,
          }
        ]);
      })
      .finally(() => {
        setIsTyping(false);
      });
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] md:h-[calc(100vh-2rem)]">
      {/* Chat Header */}
      <div className="flex justify-between items-center px-6 py-4 border-b border-zinc-800/50 bg-zinc-900/30 backdrop-blur-md rounded-t-2xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-violet-500 to-teal-500 flex items-center justify-center shadow-lg shadow-violet-500/20">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-white font-medium">AGI Orchestrator</h2>
            <p className="text-xs text-emerald-400 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Online & Ready
            </p>
          </div>
        </div>
        <button className="p-2 text-zinc-400 hover:text-white transition-colors">
          <MoreVertical className="w-5 h-5" />
        </button>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-zinc-900/10">
        {messages.map((msg, i) => (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            key={msg.id}
            className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
          >
            <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
              msg.role === "user" 
                ? "bg-zinc-800 border border-zinc-700" 
                : "bg-gradient-to-br from-violet-500 to-teal-500 shadow-md shadow-violet-500/20"
            }`}>
              {msg.role === "user" ? <User className="w-4 h-4 text-zinc-300" /> : <Brain className="w-4 h-4 text-white" />}
            </div>
            
            <div className={`max-w-[80%] rounded-2xl px-5 py-3 ${
              msg.role === "user" 
                ? "bg-violet-600 text-white" 
                : "bg-zinc-800/80 text-zinc-200 border border-zinc-700/50"
            }`}>
              <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>
            </div>
          </motion.div>
        ))}

        {isTyping && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-4">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-violet-500 to-teal-500 flex items-center justify-center shrink-0">
              <Brain className="w-4 h-4 text-white" />
            </div>
            <div className="bg-zinc-800/80 border border-zinc-700/50 rounded-2xl px-5 py-4 flex gap-1">
              <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-2 h-2 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
          </motion.div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-zinc-900/30 backdrop-blur-md border-t border-zinc-800/50 rounded-b-2xl">
        <form onSubmit={handleSend} className="relative flex items-center">
          <button type="button" className="absolute left-4 p-2 text-zinc-400 hover:text-white transition-colors">
            <Paperclip className="w-5 h-5" />
          </button>
          
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Give the AGI a goal or ask a question..."
            className="w-full bg-zinc-800/50 border border-zinc-700 text-white rounded-xl py-4 pl-14 pr-14 focus:outline-none focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 transition-all placeholder:text-zinc-500"
          />
          
          <button 
            type="submit" 
            disabled={!input.trim() || isTyping}
            className="absolute right-2 p-2 bg-violet-600 hover:bg-violet-500 disabled:bg-zinc-700 disabled:text-zinc-500 text-white rounded-lg transition-colors flex items-center justify-center"
          >
            {isTyping ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          </button>
        </form>
        <p className="text-center text-xs text-zinc-500 mt-3">
          The AGI may take time to execute complex goals. Background tasks can be monitored in the Dashboard.
        </p>
      </div>
    </div>
  );
}
