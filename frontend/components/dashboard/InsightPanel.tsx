"use client";

import { motion } from "framer-motion";
import { TrendingUp, AlertTriangle, Lightbulb, BarChart2, ArrowUpRight, ArrowDownRight } from "lucide-react";
import type { Insight } from "@/lib/types";

interface Props {
  insights: Insight[];
  executiveSummary: string;
  narrative: string;
}

const IMPACT_STYLE = {
  high: "bg-red-950/30 border-red-500/30 text-red-400",
  medium: "bg-amber-950/30 border-amber-500/30 text-amber-400",
  low: "bg-slate-800/30 border-slate-600/30 text-slate-400",
};

const CATEGORY_ICON: Record<string, typeof Lightbulb> = {
  executive: Lightbulb,
  statistical: BarChart2,
  anomaly: AlertTriangle,
  forecast: TrendingUp,
  revenue: TrendingUp,
  growth: TrendingUp,
  risk: AlertTriangle,
  opportunity: Lightbulb,
};

export default function InsightPanel({ insights, executiveSummary, narrative }: Props) {
  const sorted = [...insights].sort((a, b) => {
    const order = { high: 0, medium: 1, low: 2 };
    return (order[a.impact] ?? 2) - (order[b.impact] ?? 2);
  });

  return (
    <div className="space-y-6">
      {/* Executive Summary */}
      {executiveSummary && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass rounded-xl p-6 border border-indigo-500/20"
        >
          <h3 className="font-semibold text-indigo-400 mb-3 flex items-center gap-2">
            <Lightbulb className="w-4 h-4" />
            Executive Summary
          </h3>
          <p className="text-sm text-slate-300 leading-relaxed">{executiveSummary}</p>
        </motion.div>
      )}

      {/* AI Insights */}
      <div>
        <h3 className="text-sm font-semibold text-slate-400 mb-3 flex items-center gap-2">
          <BarChart2 className="w-4 h-4 text-indigo-400" />
          AI-Generated Insights ({insights.length})
        </h3>
        <div className="space-y-3">
          {sorted.slice(0, 10).map((insight, i) => {
            const Icon = CATEGORY_ICON[insight.category] || Lightbulb;
            const impactStyle = IMPACT_STYLE[insight.impact] || IMPACT_STYLE.low;
            const hasChange = insight.change_percentage !== undefined;
            const isPositive = (insight.change_percentage ?? 0) > 0;

            return (
              <motion.div
                key={insight.insight_id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="insight-card rounded-xl p-4"
              >
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-indigo-500/15 flex items-center justify-center shrink-0 mt-0.5">
                    <Icon className="w-4 h-4 text-indigo-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <span className="text-sm font-medium text-white leading-tight">{insight.title}</span>
                      <span className={`px-2 py-0.5 rounded-full text-xs border ${impactStyle}`}>
                        {insight.impact} impact
                      </span>
                      {hasChange && (
                        <span className={`flex items-center gap-0.5 text-xs font-medium ${isPositive ? "text-emerald-400" : "text-red-400"}`}>
                          {isPositive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                          {Math.abs(insight.change_percentage!).toFixed(1)}%
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-400 mb-2 leading-relaxed">{insight.description}</p>
                    {insight.evidence?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-2">
                        {insight.evidence.map((e, j) => (
                          <span key={j} className="px-2 py-0.5 rounded text-xs bg-slate-700/50 text-slate-400">{e}</span>
                        ))}
                      </div>
                    )}
                    <div className="bg-slate-800/40 rounded-lg px-3 py-2">
                      <p className="text-xs text-slate-500">
                        <span className="text-emerald-400 font-medium">Recommendation: </span>
                        {insight.recommendation}
                      </p>
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Strategic Narrative */}
      {narrative && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="glass rounded-xl p-6 border border-cyan-500/20"
        >
          <h3 className="font-semibold text-cyan-400 mb-3 flex items-center gap-2">
            <TrendingUp className="w-4 h-4" />
            Strategic Narrative
          </h3>
          <div className="space-y-3 text-sm text-slate-300 leading-relaxed">
            {narrative.split("\n").filter(Boolean).map((para, i) => (
              <p key={i}>{para}</p>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
}
