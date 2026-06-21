"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  BarChart3, Brain, Sparkles, Upload, Database, Globe,
  FileSpreadsheet, FileText, Zap, TrendingUp, Shield, Download
} from "lucide-react";
import DataSourcePanel from "@/components/upload/DataSourcePanel";
import toast from "react-hot-toast";

const FEATURES = [
  { icon: Brain, title: "6 AI Agents", desc: "Ingestion → Understanding → Quality → BI → Insights → Dashboard" },
  { icon: BarChart3, title: "Auto KPI Engine", desc: "Revenue, Profit, Growth, Churn — auto-detected & computed" },
  { icon: Sparkles, title: "GPT-4o Insights", desc: "Executive narratives, anomaly alerts, strategic recommendations" },
  { icon: TrendingUp, title: "ML Forecasting", desc: "Prophet time-series, regression, anomaly detection" },
  { icon: Download, title: "Full Export Suite", desc: "Power BI template, PDF, PPTX, Excel, DAX measures" },
  { icon: Shield, title: "Enterprise Grade", desc: "McKinsey/BCG quality visuals, star schema data model" },
];

const DATA_SOURCES = [
  { icon: FileSpreadsheet, label: "Excel / CSV" },
  { icon: FileText, label: "PDF / Word" },
  { icon: Globe, label: "URL / Kaggle / GitHub" },
  { icon: Database, label: "Database" },
];

const DOMAINS = [
  "Sales", "Financial", "HR", "Marketing", "Healthcare",
  "Retail", "Supply Chain", "Real Estate", "Manufacturing", "Banking",
];

export default function HomePage() {
  const router = useRouter();
  const [isStarted, setIsStarted] = useState(false);

  const handleJobCreated = (jobId: string) => {
    toast.success("Analysis pipeline started!");
    router.push(`/analysis/${jobId}`);
  };

  return (
    <div className="min-h-screen bg-[#0F172A] text-white overflow-x-hidden">
      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 glass border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-indigo-500 to-cyan-400 rounded-lg flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg gradient-text">PowerBI Genius AI</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm text-slate-400">
            <span className="hover:text-white cursor-pointer transition-colors">Features</span>
            <span className="hover:text-white cursor-pointer transition-colors">Domains</span>
            <span className="hover:text-white cursor-pointer transition-colors">Pricing</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-800/50 px-3 py-1.5 rounded-full border border-slate-700">
            <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
            AI Ready
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-16 px-6 relative">
        <div className="absolute inset-0 bg-gradient-radial from-indigo-950/30 via-transparent to-transparent" />
        <div className="max-w-6xl mx-auto text-center relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-indigo-500/30 bg-indigo-950/50 text-sm text-indigo-300 mb-8"
          >
            <Sparkles className="w-4 h-4" />
            Powered by GPT-4o + LangGraph Multi-Agent Pipeline
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-5xl md:text-7xl font-bold mb-6 leading-tight"
          >
            Upload Any Dataset.
            <br />
            <span className="gradient-text">Get a McKinsey-Grade</span>
            <br />
            Power BI Dashboard.
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="text-xl text-slate-400 mb-12 max-w-3xl mx-auto"
          >
            No dashboards skills required. Our 6-agent AI system automatically cleans your data,
            detects your business domain, generates KPIs & insights, and builds a
            stakeholder-ready interactive Power BI dashboard in minutes.
          </motion.p>

          {/* Data source chips */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="flex flex-wrap justify-center gap-3 mb-10"
          >
            {DATA_SOURCES.map(({ icon: Icon, label }) => (
              <div key={label} className="flex items-center gap-2 px-4 py-2 rounded-full bg-slate-800/60 border border-slate-700 text-sm text-slate-300">
                <Icon className="w-4 h-4 text-indigo-400" />
                {label}
              </div>
            ))}
          </motion.div>

          {/* Upload Panel */}
          {!isStarted ? (
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
            >
              <DataSourcePanel onJobCreated={handleJobCreated} />
            </motion.div>
          ) : null}
        </div>
      </section>

      {/* Domain badges */}
      <section className="py-8 px-6">
        <div className="max-w-5xl mx-auto">
          <p className="text-center text-slate-500 text-sm mb-4">Auto-detects 16+ business domains</p>
          <div className="flex flex-wrap justify-center gap-2">
            {DOMAINS.map((d) => (
              <span key={d} className="px-3 py-1 rounded-full text-xs border border-slate-700 bg-slate-800/40 text-slate-400">
                {d}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-4">Enterprise AI Pipeline</h2>
            <p className="text-slate-400">6 specialized agents working in sequence to deliver Fortune 500-quality analytics</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map(({ icon: Icon, title, desc }, i) => (
              <motion.div
                key={title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.1 }}
                className="glass rounded-xl p-6 hover:border-indigo-500/40 transition-all cursor-default"
              >
                <div className="w-10 h-10 bg-gradient-to-br from-indigo-500/20 to-cyan-500/20 rounded-lg flex items-center justify-center mb-4 border border-indigo-500/20">
                  <Icon className="w-5 h-5 text-indigo-400" />
                </div>
                <h3 className="font-semibold mb-2">{title}</h3>
                <p className="text-slate-400 text-sm">{desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pipeline visualization */}
      <section className="py-16 px-6 border-t border-slate-800">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-2xl font-bold mb-10">The 6-Agent Pipeline</h2>
          <div className="flex flex-wrap justify-center gap-2 items-center">
            {[
              "1. Ingest", "→", "2. Understand", "→", "3. Quality", "→",
              "4. BI Agent", "→", "5. Insights", "→", "6. Dashboard"
            ].map((step, i) => (
              <span
                key={i}
                className={step === "→" ? "text-slate-600" : "px-3 py-2 rounded-lg text-sm font-medium bg-indigo-950/60 border border-indigo-500/20 text-indigo-300"}
              >
                {step}
              </span>
            ))}
          </div>
          <p className="text-slate-500 text-sm mt-6">
            Each agent runs autonomously, passing enriched state to the next. Powered by LangGraph orchestration.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-10 px-6">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-indigo-400" />
            <span className="font-semibold gradient-text">PowerBI Genius AI</span>
          </div>
          <p className="text-slate-500 text-sm">McKinsey-grade dashboards. Zero BI expertise required.</p>
          <div className="flex items-center gap-1 text-xs text-slate-600">
            <Zap className="w-3 h-3" />
            Powered by GPT-4o + LangGraph
          </div>
        </div>
      </footer>
    </div>
  );
}
