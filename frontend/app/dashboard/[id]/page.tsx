"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  BarChart3, ChevronLeft, Download, MessageSquare,
  Shield, Brain, Layers, LayoutDashboard, TrendingUp,
  Users, Package, Sparkles, Database, AlertCircle,
  BookOpen, RefreshCw
} from "lucide-react";
import KPICards from "@/components/dashboard/KPICards";
import ChartGrid from "@/components/dashboard/ChartGrid";
import InsightPanel from "@/components/dashboard/InsightPanel";
import ExportPanel from "@/components/dashboard/ExportPanel";
import NLQueryChat from "@/components/chat/NLQueryChat";
import { getResult, getStatus } from "@/lib/api";
import type { AnalysisResult } from "@/lib/types";

interface Props {
  params: Promise<{ id: string }>;
}

type Panel = "charts" | "insights" | "export" | "chat" | "quality" | "model";

const PAGE_ICONS: Record<string, typeof BarChart3> = {
  "Executive Overview": LayoutDashboard,
  "Trend Analysis": TrendingUp,
  "Geographic Analysis": Users,
  "Segmentation Analysis": Package,
  "Detailed Analysis": Database,
  "AI Insights & Recommendations": Sparkles,
};

export default function DashboardPage({ params }: Props) {
  const router = useRouter();
  const [jobId, setJobId] = useState("");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activePage, setActivePage] = useState(1);
  const [activePanel, setActivePanel] = useState<Panel>("charts");

  useEffect(() => {
    params.then(({ id }) => setJobId(id));
  }, [params]);

  useEffect(() => {
    if (!jobId) return;
    const load = async () => {
      try {
        // Check if completed first
        const status = await getStatus(jobId);
        if (!status.completed && !status.failed) {
          router.push(`/analysis/${jobId}`);
          return;
        }
        const data = await getResult(jobId);
        setResult(data);
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Failed to load results";
        setError(msg);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [jobId, router]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0F172A] flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="w-10 h-10 text-indigo-400 animate-spin mx-auto mb-4" />
          <p className="text-slate-400">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="min-h-screen bg-[#0F172A] flex items-center justify-center">
        <div className="text-center max-w-md">
          <AlertCircle className="w-10 h-10 text-red-400 mx-auto mb-4" />
          <p className="text-white font-semibold mb-2">Dashboard Not Ready</p>
          <p className="text-slate-400 text-sm mb-4">{error || "Results not available yet."}</p>
          <button
            onClick={() => router.push(`/analysis/${jobId}`)}
            className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm"
          >
            Back to Analysis
          </button>
        </div>
      </div>
    );
  }

  const { dashboard_spec, kpis, insights, executive_summary, narrative, domain, quality_report, data_model } = result;
  const pages = dashboard_spec?.pages || [];
  const colorPalette = dashboard_spec?.color_palette || ["#6366F1", "#22D3EE", "#10B981", "#F59E0B"];

  const SIDE_PANELS = [
    { id: "charts" as Panel, icon: BarChart3, label: "Charts" },
    { id: "insights" as Panel, icon: Brain, label: "Insights" },
    { id: "chat" as Panel, icon: MessageSquare, label: "Ask AI" },
    { id: "export" as Panel, icon: Download, label: "Export" },
    { id: "quality" as Panel, icon: Shield, label: "Quality" },
    { id: "model" as Panel, icon: Layers, label: "Data Model" },
  ];

  return (
    <div className="min-h-screen bg-[#0F172A] text-white flex flex-col">
      {/* Top Navigation */}
      <nav className="border-b border-slate-800 px-4 h-14 flex items-center gap-3 shrink-0">
        <button onClick={() => router.push("/")} className="p-2 hover:bg-slate-800 rounded-lg transition-colors">
          <ChevronLeft className="w-4 h-4 text-slate-400" />
        </button>
        <div className="w-7 h-7 bg-gradient-to-br from-indigo-500 to-cyan-400 rounded-lg flex items-center justify-center">
          <BarChart3 className="w-4 h-4" />
        </div>
        <span className="font-semibold gradient-text text-sm">PowerBI Genius AI</span>

        <div className="mx-2 text-slate-700">|</div>
        <div>
          <span className="font-semibold text-sm text-white">{dashboard_spec?.title || "AI Dashboard"}</span>
          <span className="ml-2 px-2 py-0.5 rounded-full text-xs bg-indigo-950/60 border border-indigo-500/30 text-indigo-300">
            {domain?.toUpperCase()}
          </span>
        </div>

        <div className="ml-auto flex items-center gap-3">
          <div className="hidden md:flex items-center gap-1 text-xs text-slate-500">
            <Shield className="w-3 h-3 text-emerald-400" />
            Quality: <span className="text-emerald-400 font-medium">{quality_report?.overall_score?.toFixed(0)}%</span>
          </div>
          <div className="hidden md:flex items-center gap-1 text-xs text-slate-500">
            <BookOpen className="w-3 h-3 text-indigo-400" />
            {result.data_model?.dax_measures?.length || 0} DAX measures
          </div>
          <button
            onClick={() => setActivePanel("export")}
            className="flex items-center gap-2 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 rounded-lg text-xs font-medium transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            Export
          </button>
        </div>
      </nav>

      <div className="flex flex-1 overflow-hidden">
        {/* Left sidebar — page navigation */}
        <div className="w-52 border-r border-slate-800 overflow-y-auto shrink-0 hidden md:flex flex-col py-3 gap-1 px-2">
          <p className="text-xs text-slate-600 px-2 mb-1 font-medium uppercase tracking-wider">Pages</p>
          {pages.map((page) => {
            const Icon = PAGE_ICONS[page.title] || BarChart3;
            return (
              <button
                key={page.page_number}
                onClick={() => { setActivePage(page.page_number); setActivePanel("charts"); }}
                className={`flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-xs font-medium transition-all text-left ${
                  activePage === page.page_number && activePanel === "charts"
                    ? "bg-indigo-950/60 border border-indigo-500/30 text-indigo-300"
                    : "text-slate-500 hover:text-slate-300 hover:bg-slate-800/40"
                }`}
              >
                <Icon className="w-3.5 h-3.5 shrink-0" />
                <span className="truncate">{page.title}</span>
              </button>
            );
          })}

          <div className="border-t border-slate-800 mt-3 pt-3">
            <p className="text-xs text-slate-600 px-2 mb-1 font-medium uppercase tracking-wider">Tools</p>
            {SIDE_PANELS.filter(p => p.id !== "charts").map(({ id, icon: Icon, label }) => (
              <button
                key={id}
                onClick={() => setActivePanel(id)}
                className={`w-full flex items-center gap-2.5 px-3 py-2.5 rounded-lg text-xs font-medium transition-all text-left ${
                  activePanel === id
                    ? "bg-indigo-950/60 border border-indigo-500/30 text-indigo-300"
                    : "text-slate-500 hover:text-slate-300 hover:bg-slate-800/40"
                }`}
              >
                <Icon className="w-3.5 h-3.5 shrink-0" />
                {label}
              </button>
            ))}
          </div>

          {/* Bookmarks */}
          {dashboard_spec?.bookmarks?.length > 0 && (
            <div className="border-t border-slate-800 mt-3 pt-3">
              <p className="text-xs text-slate-600 px-2 mb-1 font-medium uppercase tracking-wider">Bookmarks</p>
              {dashboard_spec.bookmarks.map((bm) => (
                <button
                  key={bm.name}
                  onClick={() => { setActivePage(parseInt(bm.page.split(",")[0])); setActivePanel("charts"); }}
                  className="w-full text-left px-3 py-2 rounded-lg text-xs text-slate-500 hover:text-slate-300 hover:bg-slate-800/40 transition-all truncate"
                >
                  ⌖ {bm.name}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Main content */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
          {/* KPI Cards — always visible */}
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-semibold text-slate-400">Key Performance Indicators</h2>
              <span className="text-xs text-slate-600">{kpis.length} KPIs generated</span>
            </div>
            <KPICards kpis={kpis} />
          </motion.div>

          {/* Panel content */}
          {activePanel === "charts" && (
            <motion.div key={`charts-${activePage}`} initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-slate-400">
                  {pages.find(p => p.page_number === activePage)?.title || "Dashboard"}
                </h2>
                <p className="text-xs text-slate-600">
                  {pages.find(p => p.page_number === activePage)?.description}
                </p>
              </div>
              <ChartGrid
                pages={pages}
                activePage={activePage}
                jobId={jobId}
                colorPalette={colorPalette}
              />
            </motion.div>
          )}

          {activePanel === "insights" && (
            <motion.div key="insights" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
              <InsightPanel
                insights={insights}
                executiveSummary={executive_summary}
                narrative={narrative}
              />
            </motion.div>
          )}

          {activePanel === "chat" && (
            <motion.div key="chat" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              className="glass rounded-2xl p-6 min-h-[600px] flex flex-col"
            >
              <NLQueryChat jobId={jobId} />
            </motion.div>
          )}

          {activePanel === "export" && (
            <motion.div key="export" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              className="glass rounded-2xl p-6"
            >
              <ExportPanel jobId={jobId} domain={domain || "business"} />
            </motion.div>
          )}

          {activePanel === "quality" && quality_report && (
            <motion.div key="quality" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              className="space-y-4"
            >
              <div className="glass rounded-xl p-6">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <Shield className="w-4 h-4 text-indigo-400" />
                  Data Quality Report
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                  {[
                    { label: "Overall Score", value: `${quality_report.overall_score?.toFixed(0)}%`, good: quality_report.overall_score >= 70 },
                    { label: "Missing Values", value: `${quality_report.missing_value_score?.toFixed(0)}%`, good: quality_report.missing_value_score >= 80 },
                    { label: "Duplicates", value: `${quality_report.duplicate_score?.toFixed(0)}%`, good: quality_report.duplicate_score >= 90 },
                    { label: "Outliers", value: `${quality_report.outlier_score?.toFixed(0)}%`, good: quality_report.outlier_score >= 80 },
                  ].map(({ label, value, good }) => (
                    <div key={label} className={`rounded-lg p-3 border ${good ? "border-emerald-500/30 bg-emerald-950/20" : "border-amber-500/30 bg-amber-950/20"}`}>
                      <p className="text-xs text-slate-500 mb-1">{label}</p>
                      <p className={`text-2xl font-bold ${good ? "text-emerald-400" : "text-amber-400"}`}>{value}</p>
                    </div>
                  ))}
                </div>
                <div className="text-xs text-slate-500 mb-3">
                  Dataset: <span className="text-white">{quality_report.total_rows?.toLocaleString()} rows</span> ×{" "}
                  <span className="text-white">{quality_report.total_columns} columns</span>{" "}
                  · <span className="text-amber-400">{quality_report.duplicate_count} duplicates removed</span>
                </div>
                <div className="space-y-2 max-h-64 overflow-y-auto">
                  {quality_report.issues?.slice(0, 10).map((issue, i) => (
                    <div key={i} className={`rounded-lg px-3 py-2 text-xs border ${
                      issue.severity === "critical" ? "border-red-500/30 bg-red-950/20" :
                      issue.severity === "high" ? "border-orange-500/30 bg-orange-950/20" :
                      issue.severity === "medium" ? "border-amber-500/30 bg-amber-950/20" :
                      "border-slate-600/30 bg-slate-800/20"
                    }`}>
                      <span className="font-medium capitalize text-slate-300">{issue.issue_type.replace("_", " ")}</span>
                      {issue.column && <span className="text-indigo-400 ml-1">({issue.column})</span>}
                      <p className="text-slate-500 mt-0.5">{issue.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {activePanel === "model" && data_model && (
            <motion.div key="model" initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              className="space-y-4"
            >
              <div className="glass rounded-xl p-6">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <Layers className="w-4 h-4 text-indigo-400" />
                  Star Schema Data Model
                </h3>
                <div className="grid md:grid-cols-2 gap-4 mb-6">
                  <div>
                    <p className="text-xs text-slate-500 mb-2">Fact Tables</p>
                    {data_model.fact_tables?.map((t) => (
                      <span key={t} className="inline-block mr-2 mb-2 px-2 py-1 rounded bg-indigo-950/50 border border-indigo-500/30 text-xs text-indigo-300">{t}</span>
                    ))}
                  </div>
                  <div>
                    <p className="text-xs text-slate-500 mb-2">Dimension Tables</p>
                    {data_model.dimension_tables?.map((t) => (
                      <span key={t} className="inline-block mr-2 mb-2 px-2 py-1 rounded bg-slate-800/50 border border-slate-600 text-xs text-slate-300">{t}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="text-xs text-slate-500 mb-2">DAX Measures ({data_model.dax_measures?.length || 0})</p>
                  <div className="space-y-2 max-h-96 overflow-y-auto font-mono">
                    {data_model.dax_measures?.slice(0, 15).map((m, i) => (
                      <div key={i} className="rounded-lg bg-slate-900/60 border border-slate-700/40 p-3">
                        <p className="text-xs text-cyan-400 mb-1">{m.name}</p>
                        <p className="text-xs text-slate-400 whitespace-pre-wrap">{m.expression}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* Mobile bottom tabs */}
      <div className="md:hidden border-t border-slate-800 flex">
        {SIDE_PANELS.map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            onClick={() => setActivePanel(id)}
            className={`flex-1 flex flex-col items-center gap-1 py-2 text-xs transition-colors ${
              activePanel === id ? "text-indigo-400" : "text-slate-600"
            }`}
          >
            <Icon className="w-4 h-4" />
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}
