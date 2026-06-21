"use client";

import { useState, useRef, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot, User, Sparkles, Loader2, MessageSquare } from "lucide-react";
import { sendQuery, getChatSuggestions } from "@/lib/api";
import type { ChatMessage } from "@/lib/types";
import toast from "react-hot-toast";

interface Props {
  jobId: string;
}

export default function NLQueryChat({ jobId }: Props) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getChatSuggestions(jobId).then((d) => setSuggestions(d.suggestions || [])).catch(() => {});

    setMessages([{
      role: "assistant",
      content: "Hello! I'm your AI data analyst. Ask me anything about your dataset — trends, comparisons, forecasts, or specific metrics. I have full context of your data.",
      follow_up_questions: [],
      timestamp: new Date(),
    }]);
  }, [jobId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim() || loading) return;

    const userMsg: ChatMessage = { role: "user", content: text, timestamp: new Date() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const history = messages.map((m) => ({ role: m.role, content: m.content }));
      const res = await sendQuery(jobId, text, history);

      const assistantMsg: ChatMessage = {
        role: "assistant",
        content: res.answer,
        chart_suggestion: res.chart_suggestion,
        follow_up_questions: res.follow_up_questions || [],
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
      setSuggestions(res.follow_up_questions || []);
    } catch {
      toast.error("Query failed. Please try again.");
      setMessages((prev) => prev.filter((m) => m !== userMsg));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Chat header */}
      <div className="flex items-center gap-3 mb-4 pb-4 border-b border-slate-700/50">
        <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-cyan-400 rounded-lg flex items-center justify-center">
          <MessageSquare className="w-4 h-4 text-white" />
        </div>
        <div>
          <p className="font-semibold text-sm text-white">AI Data Analyst</p>
          <p className="text-xs text-slate-500">Ask anything about your dashboard</p>
        </div>
        <div className="ml-auto flex items-center gap-1 text-xs text-emerald-400">
          <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
          GPT-4o
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-4 pr-1 min-h-0">
        <AnimatePresence initial={false}>
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : ""}`}
            >
              <div className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 ${
                msg.role === "user" ? "bg-indigo-500/20" : "bg-slate-700/50"
              }`}>
                {msg.role === "user"
                  ? <User className="w-4 h-4 text-indigo-400" />
                  : <Bot className="w-4 h-4 text-slate-400" />
                }
              </div>
              <div className={`flex flex-col gap-2 max-w-[85%] ${msg.role === "user" ? "items-end" : "items-start"}`}>
                <div className={`px-4 py-3 rounded-xl text-sm leading-relaxed ${
                  msg.role === "user"
                    ? "bg-indigo-600/80 text-white rounded-tr-sm"
                    : "bg-slate-800/60 text-slate-200 rounded-tl-sm"
                }`}>
                  {msg.content}
                </div>

                {/* Chart suggestion badge */}
                {msg.chart_suggestion && (
                  <div className="px-3 py-1.5 rounded-lg bg-cyan-950/40 border border-cyan-500/20 text-xs text-cyan-400">
                    <Sparkles className="w-3 h-3 inline mr-1" />
                    Suggested: {msg.chart_suggestion.chart_type} chart — {msg.chart_suggestion.title}
                  </div>
                )}

                {/* Follow-up questions */}
                {msg.follow_up_questions && msg.follow_up_questions.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-1">
                    {msg.follow_up_questions.slice(0, 3).map((q, j) => (
                      <button
                        key={j}
                        onClick={() => sendMessage(q)}
                        className="text-xs px-2 py-1 rounded-full border border-slate-600 text-slate-400 hover:text-white hover:border-indigo-500 transition-all"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {loading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
            <div className="w-7 h-7 rounded-lg bg-slate-700/50 flex items-center justify-center">
              <Bot className="w-4 h-4 text-slate-400" />
            </div>
            <div className="px-4 py-3 rounded-xl bg-slate-800/60 flex items-center gap-2">
              <Loader2 className="w-4 h-4 text-indigo-400 animate-spin" />
              <span className="text-xs text-slate-400">Analyzing...</span>
            </div>
          </motion.div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {suggestions.length > 0 && messages.length <= 2 && (
        <div className="mt-3 mb-2">
          <p className="text-xs text-slate-500 mb-2">Try asking:</p>
          <div className="flex flex-col gap-1.5">
            {suggestions.slice(0, 4).map((s, i) => (
              <button
                key={i}
                onClick={() => sendMessage(s)}
                className="text-left text-xs px-3 py-2 rounded-lg border border-slate-700 bg-slate-800/30 text-slate-400 hover:text-white hover:border-indigo-500/50 transition-all truncate"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="mt-4 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendMessage(input)}
          placeholder="Ask about your data..."
          disabled={loading}
          className="flex-1 bg-slate-800/60 border border-slate-600 rounded-xl px-4 py-3 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 disabled:opacity-60"
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={!input.trim() || loading}
          className="w-12 h-12 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-xl flex items-center justify-center transition-all"
        >
          <Send className="w-4 h-4 text-white" />
        </button>
      </div>
    </div>
  );
}
