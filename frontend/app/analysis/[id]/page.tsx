"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { BarChart3, ArrowRight, RefreshCw } from "lucide-react";
import AgentProgress from "@/components/pipeline/AgentProgress";
import { createProgressWS, getStatus } from "@/lib/api";
import type { AnalysisStatus } from "@/lib/types";
import toast from "react-hot-toast";

interface Props {
  params: Promise<{ id: string }>;
}

const AI_TIPS = [
  "Detecting business domain from column patterns and sample data...",
  "Running IQR, Z-Score & Isolation Forest outlier detection...",
  "Computing YoY growth, rolling averages & DAX measures...",
  "Generating GPT-4o executive insights & recommendations...",
  "Designing 6-page stakeholder-ready Power BI dashboard...",
  "Building star schema data model with relationships...",
];

export default function AnalysisPage({ params }: Props) {
  const router = useRouter();
  const [jobId, setJobId] = useState<string>("");
  const [status, setStatus] = useState<AnalysisStatus | null>(null);
  const [tipIndex, setTipIndex] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    params.then(({ id }) => setJobId(id));
  }, [params]);

  useEffect(() => {
    if (!jobId) return;

    // Rotate tips
    const tipTimer = setInterval(() => setTipIndex((i) => (i + 1) % AI_TIPS.length), 3500);

    // Try WebSocket first, fall back to polling
    try {
      const ws = createProgressWS(jobId, (data: unknown) => {
        const d = data as AnalysisStatus;
        setStatus(d);
        if (d.completed) {
          clearInterval(tipTimer);
          ws.close();
          toast.success("Dashboard ready!");
          setTimeout(() => router.push(`/dashboard/${jobId}`), 1000);
        }
        if (d.failed) {
          clearInterval(tipTimer);
          ws.close();
          toast.error("Pipeline encountered errors. Redirecting to results...");
          setTimeout(() => router.push(`/dashboard/${jobId}`), 2000);
        }
      });
      wsRef.current = ws;
    } catch {
      // Polling fallback
      const poll = setInterval(async () => {
        const s = await getStatus(jobId);
        setStatus(s);
        if (s.completed || s.failed) {
          clearInterval(poll);
          clearInterval(tipTimer);
          router.push(`/dashboard/${jobId}`);
        }
      }, 2000);
      return () => { clearInterval(poll); clearInterval(tipTimer); };
    }

    return () => {
      clearInterval(tipTimer);
      wsRef.current?.close();
    };
  }, [jobId, router]);

  return (
    <div className="min-h-screen bg-[#0F172A] text-white flex flex-col">
      {/* Nav */}
      <nav className="border-b border-slate-800 px-6 h-14 flex items-center gap-3">
        <div className="w-7 h-7 bg-gradient-to-br from-indigo-500 to-cyan-400 rounded-lg flex items-center justify-center">
          <BarChart3 className="w-4 h-4" />
        </div>
        <span className="font-semibold gradient-text">PowerBI Genius AI</span>
        <span className="text-slate-600 text-sm ml-2">/ Analysis</span>
      </nav>

      <div className="flex-1 max-w-2xl mx-auto w-full px-6 py-12">
        {/* Header */}
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="text-center mb-10">
          <div className="w-16 h-16 bg-gradient-to-br from-indigo-500/20 to-cyan-500/20 rounded-2xl flex items-center justify-center mx-auto mb-4 border border-indigo-500/20">
            <BarChart3 className="w-8 h-8 text-indigo-400 animate-pulse-slow" />
          </div>
          <h1 className="text-2xl font-bold mb-2">AI Pipeline Running</h1>
          <p className="text-slate-400 text-sm">
            6 specialized agents are analyzing your dataset in sequence
          </p>
          {jobId && (
            <p className="text-xs text-slate-600 mt-2 font-mono">Job ID: {jobId}</p>
          )}
        </motion.div>

        {/* AI Tip Ticker */}
        <motion.div
          key={tipIndex}
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0 }}
          className="mb-8 text-center px-4 py-3 rounded-xl border border-indigo-500/20 bg-indigo-950/20"
        >
          <p className="text-xs text-indigo-300 italic">{AI_TIPS[tipIndex]}</p>
        </motion.div>

        {/* Agent Progress */}
        {status ? (
          <AgentProgress
            progress={status.progress}
            currentAgent={status.current_agent}
            agentStatuses={status.agent_statuses}
            errors={status.errors}
          />
        ) : (
          <div className="glass rounded-2xl p-8 text-center">
            <RefreshCw className="w-8 h-8 text-slate-500 animate-spin mx-auto mb-3" />
            <p className="text-slate-500 text-sm">Connecting to pipeline...</p>
          </div>
        )}

        {/* Completion hint */}
        {status?.progress && status.progress >= 90 && !status.completed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="mt-6 text-center"
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-950/40 border border-emerald-500/30 text-emerald-400 text-sm">
              <ArrowRight className="w-4 h-4" />
              Almost done — finalizing your dashboard...
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
