"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle2, Loader2, XCircle, Clock,
  HardDrive, Brain, Shield, TrendingUp, Lightbulb, LayoutDashboard
} from "lucide-react";

interface AgentStatuses {
  ingestion_agent: string;
  understanding_agent: string;
  quality_agent: string;
  bi_agent: string;
  insight_agent: string;
  dashboard_agent: string;
}

interface Props {
  progress: number;
  currentAgent: string | null;
  agentStatuses: AgentStatuses;
  errors: string[];
}

const AGENTS = [
  {
    key: "ingestion_agent",
    icon: HardDrive,
    label: "Data Ingestion",
    desc: "Reading & parsing your dataset",
    step: 1,
  },
  {
    key: "understanding_agent",
    icon: Brain,
    label: "Domain Detection",
    desc: "Identifying business context & entities",
    step: 2,
  },
  {
    key: "quality_agent",
    icon: Shield,
    label: "Data Quality",
    desc: "Detecting missing values, outliers & duplicates",
    step: 3,
  },
  {
    key: "bi_agent",
    icon: TrendingUp,
    label: "BI & KPIs",
    desc: "Computing metrics, DAX measures & data model",
    step: 4,
  },
  {
    key: "insight_agent",
    icon: Lightbulb,
    label: "AI Insights",
    desc: "Generating executive narratives & forecasts",
    step: 5,
  },
  {
    key: "dashboard_agent",
    icon: LayoutDashboard,
    label: "Dashboard Design",
    desc: "Building 6-page stakeholder dashboard",
    step: 6,
  },
] as const;

function StatusIcon({ status }: { status: string }) {
  if (status === "completed") return <CheckCircle2 className="w-5 h-5 text-emerald-400" />;
  if (status === "running") return <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />;
  if (status === "failed") return <XCircle className="w-5 h-5 text-red-400" />;
  return <Clock className="w-5 h-5 text-slate-600" />;
}

export default function AgentProgress({ progress, currentAgent, agentStatuses, errors }: Props) {
  return (
    <div className="space-y-6">
      {/* Overall Progress */}
      <div className="glass rounded-2xl p-6">
        <div className="flex items-center justify-between mb-3">
          <span className="text-sm font-medium text-slate-300">Pipeline Progress</span>
          <span className="text-2xl font-bold gradient-text">{progress}%</span>
        </div>
        <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-gradient-to-r from-indigo-500 to-cyan-400 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>
        {currentAgent && (
          <p className="text-xs text-slate-500 mt-2">
            Active: <span className="text-indigo-400">{currentAgent}</span>
          </p>
        )}
      </div>

      {/* Agent Steps */}
      <div className="space-y-3">
        {AGENTS.map(({ key, icon: Icon, label, desc, step }) => {
          const status = agentStatuses[key] || "pending";
          const isActive = status === "running";
          const isDone = status === "completed";
          const isFailed = status === "failed";

          return (
            <motion.div
              key={key}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: step * 0.05 }}
              className={`glass rounded-xl p-4 flex items-center gap-4 transition-all border ${
                isActive ? "agent-active border-indigo-500/40" :
                isDone ? "agent-done border-emerald-500/30" :
                isFailed ? "agent-error border-red-500/30" :
                "border-slate-700/30"
              }`}
            >
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
                isActive ? "bg-indigo-500/20" :
                isDone ? "bg-emerald-500/15" :
                isFailed ? "bg-red-500/15" :
                "bg-slate-700/40"
              }`}>
                <Icon className={`w-5 h-5 ${
                  isActive ? "text-indigo-400" :
                  isDone ? "text-emerald-400" :
                  isFailed ? "text-red-400" :
                  "text-slate-500"
                }`} />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-medium px-1.5 py-0.5 rounded text-slate-400 bg-slate-700/50`}>
                    Agent {step}
                  </span>
                  <span className={`font-medium text-sm ${
                    isActive ? "text-white" : isDone ? "text-emerald-300" : "text-slate-400"
                  }`}>{label}</span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5 truncate">{desc}</p>
              </div>

              <StatusIcon status={status} />
            </motion.div>
          );
        })}
      </div>

      {/* Errors */}
      <AnimatePresence>
        {errors.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl border border-red-500/30 bg-red-950/20 p-4"
          >
            <p className="text-sm font-medium text-red-400 mb-2">Pipeline Warnings</p>
            {errors.slice(0, 3).map((err, i) => (
              <p key={i} className="text-xs text-red-300/70 mb-1">{err}</p>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
