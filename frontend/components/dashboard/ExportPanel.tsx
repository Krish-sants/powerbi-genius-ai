"use client";

import { motion } from "framer-motion";
import { Download, FileSpreadsheet, FileText, Presentation, Code, Table2, CheckCircle } from "lucide-react";
import { useState } from "react";
import { getExportUrl } from "@/lib/api";
import toast from "react-hot-toast";

interface Props {
  jobId: string;
  domain: string;
}

const EXPORTS = [
  {
    id: "excel",
    label: "Excel Report",
    desc: "KPIs, insights, cleaned data, DAX measures",
    icon: FileSpreadsheet,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10 border-emerald-500/20",
    badge: "Recommended",
  },
  {
    id: "pdf",
    label: "PDF Report",
    desc: "Executive summary, KPIs, AI insights",
    icon: FileText,
    color: "text-red-400",
    bg: "bg-red-500/10 border-red-500/20",
  },
  {
    id: "pptx",
    label: "PowerPoint",
    desc: "Board-ready presentation with 5 slides",
    icon: Presentation,
    color: "text-orange-400",
    bg: "bg-orange-500/10 border-orange-500/20",
  },
  {
    id: "pbix-template",
    label: "Power BI Template",
    desc: "Full dashboard spec + data model JSON",
    icon: Table2,
    color: "text-yellow-400",
    bg: "bg-yellow-500/10 border-yellow-500/20",
  },
  {
    id: "dax",
    label: "DAX Measures",
    desc: "All computed DAX expressions (.dax file)",
    icon: Code,
    color: "text-cyan-400",
    bg: "bg-cyan-500/10 border-cyan-500/20",
  },
  {
    id: "csv",
    label: "Cleaned CSV",
    desc: "Cleaned, imputed, deduplicated dataset",
    icon: FileSpreadsheet,
    color: "text-indigo-400",
    bg: "bg-indigo-500/10 border-indigo-500/20",
  },
];

export default function ExportPanel({ jobId, domain }: Props) {
  const [downloaded, setDownloaded] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState<string | null>(null);

  const handleDownload = async (exportId: string) => {
    setLoading(exportId);
    try {
      const url = getExportUrl(jobId, exportId);
      const link = document.createElement("a");
      link.href = url;
      link.download = "";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      setDownloaded((prev) => new Set(Array.from(prev).concat(exportId)));
      toast.success("Download started!");
    } catch {
      toast.error("Export failed. Please try again.");
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Download className="w-4 h-4 text-indigo-400" />
        <h3 className="text-sm font-semibold text-slate-300">Export Your Dashboard</h3>
      </div>

      <div className="grid grid-cols-1 gap-3">
        {EXPORTS.map(({ id, label, desc, icon: Icon, color, bg, badge }) => (
          <motion.button
            key={id}
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.99 }}
            onClick={() => handleDownload(id)}
            disabled={loading === id}
            className={`w-full flex items-center gap-4 p-4 rounded-xl border ${bg} transition-all text-left hover:opacity-90 disabled:opacity-60`}
          >
            <div className="w-10 h-10 rounded-lg bg-slate-800/50 flex items-center justify-center shrink-0">
              {downloaded.has(id) ? (
                <CheckCircle className="w-5 h-5 text-emerald-400" />
              ) : loading === id ? (
                <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin opacity-60" />
              ) : (
                <Icon className={`w-5 h-5 ${color}`} />
              )}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-medium text-sm text-white">{label}</span>
                {badge && (
                  <span className="px-1.5 py-0.5 rounded-full text-xs bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    {badge}
                  </span>
                )}
                {downloaded.has(id) && (
                  <span className="px-1.5 py-0.5 rounded-full text-xs bg-emerald-500/20 text-emerald-400">
                    Downloaded
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 truncate">{desc}</p>
            </div>
            <Download className={`w-4 h-4 ${color} shrink-0`} />
          </motion.button>
        ))}
      </div>

      <p className="text-xs text-slate-600 text-center pt-2">
        All exports include your AI-generated insights & {domain.toUpperCase()} domain analysis
      </p>
    </div>
  );
}
