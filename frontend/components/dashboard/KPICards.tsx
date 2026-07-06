"use client";

import { motion } from "framer-motion";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";
import type { KPI } from "@/lib/types";

interface Props {
  kpis: KPI[];
}

const CATEGORY_COLORS: Record<string, string> = {
  Revenue: "from-indigo-500/20 to-indigo-600/5 border-indigo-500/30",
  Profitability: "from-emerald-500/20 to-emerald-600/5 border-emerald-500/30",
  Growth: "from-cyan-500/20 to-cyan-600/5 border-cyan-500/30",
  Customer: "from-violet-500/20 to-violet-600/5 border-violet-500/30",
  Volume: "from-amber-500/20 to-amber-600/5 border-amber-500/30",
  "Data Volume": "from-amber-500/20 to-amber-600/5 border-amber-500/30",
  Efficiency: "from-rose-500/20 to-rose-600/5 border-rose-500/30",
  Quality: "from-sky-500/20 to-sky-600/5 border-sky-500/30",
  Time: "from-teal-500/20 to-teal-600/5 border-teal-500/30",
  Concentration: "from-fuchsia-500/20 to-fuchsia-600/5 border-fuchsia-500/30",
  default: "from-slate-500/20 to-slate-600/5 border-slate-500/30",
};

const CATEGORY_TEXT: Record<string, string> = {
  Revenue: "text-indigo-400",
  Profitability: "text-emerald-400",
  Growth: "text-cyan-400",
  Customer: "text-violet-400",
  Volume: "text-amber-400",
  "Data Volume": "text-amber-400",
  Efficiency: "text-rose-400",
  Quality: "text-sky-400",
  Time: "text-teal-400",
  Concentration: "text-fuchsia-400",
  default: "text-slate-400",
};

function TrendBadge({ trend, pct }: { trend?: string; pct?: number }) {
  if (!trend || trend === "stable") return (
    <span className="flex items-center gap-1 text-xs text-slate-500">
      <Minus className="w-3 h-3" /> Stable
    </span>
  );
  const isUp = trend === "up";
  return (
    <span className={`flex items-center gap-1 text-xs font-medium ${isUp ? "text-emerald-400" : "text-red-400"}`}>
      {isUp ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
      {pct !== undefined ? `${Math.abs(pct).toFixed(1)}%` : trend}
    </span>
  );
}

export default function KPICards({ kpis }: Props) {
  const sorted = [...kpis].sort((a, b) => a.priority - b.priority).slice(0, 12);

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
      {sorted.map((kpi, i) => {
        const colorClass = CATEGORY_COLORS[kpi.category] || CATEGORY_COLORS.default;
        const textClass = CATEGORY_TEXT[kpi.category] || CATEGORY_TEXT.default;

        return (
          <motion.div
            key={kpi.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className={`relative rounded-xl p-4 bg-gradient-to-br ${colorClass} border kpi-glow overflow-hidden group hover:scale-[1.02] transition-transform cursor-default`}
            title={kpi.description}
          >
            {/* Background glow */}
            <div className="absolute top-0 right-0 w-20 h-20 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/2" />

            <div className="relative">
              <p className="text-xs text-slate-500 mb-1 truncate">{kpi.category}</p>
              <p className="text-2xl font-bold text-white mb-1 truncate">
                {kpi.formatted_value || "—"}
              </p>
              <p className={`text-xs font-medium mb-2 truncate ${textClass}`}>
                {kpi.display_name}
              </p>
              <TrendBadge trend={kpi.trend} pct={kpi.trend_percentage} />
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
