"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { motion, AnimatePresence } from "framer-motion";
import {
  Upload, Globe, Database, Link, FileSpreadsheet,
  ChevronRight, Loader2, X, CheckCircle, Sparkles
} from "lucide-react";
import toast from "react-hot-toast";
import { uploadFile, uploadUrl, uploadDatabase, uploadMultiple } from "@/lib/api";

interface Props {
  onJobCreated: (jobId: string) => void;
}

type Tab = "file" | "url" | "database" | "multiple";

const ACCEPTED = {
  "text/csv": [".csv"],
  "application/vnd.ms-excel": [".xls"],
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
  "application/json": [".json"],
  "application/pdf": [".pdf"],
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"],
  "application/xml": [".xml"],
  "text/plain": [".txt", ".tsv"],
};

export default function DataSourcePanel({ onJobCreated }: Props) {
  const [tab, setTab] = useState<Tab>("file");
  const [loading, setLoading] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [url, setUrl] = useState("");
  const [sourceType, setSourceType] = useState("url");
  const [connString, setConnString] = useState("");
  const [query, setQuery] = useState("SELECT * FROM sales LIMIT 50000");

  const onDrop = useCallback((accepted: File[]) => {
    setFiles(accepted);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    multiple: tab === "multiple",
    maxSize: 200 * 1024 * 1024,
  });

  const handleAnalyze = async () => {
    setLoading(true);
    try {
      let result: { job_id: string };

      if (tab === "file") {
        if (!files[0]) { toast.error("Please select a file"); return; }
        result = await uploadFile(files[0]);
      } else if (tab === "multiple") {
        if (!files.length) { toast.error("Please select files"); return; }
        result = await uploadMultiple(files);
      } else if (tab === "url") {
        if (!url.trim()) { toast.error("Please enter a URL"); return; }
        result = await uploadUrl(url.trim(), sourceType);
      } else {
        if (!connString.trim()) { toast.error("Please enter connection string"); return; }
        result = await uploadDatabase(connString, query);
      }

      onJobCreated(result.job_id);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Upload failed";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  const tabs: { id: Tab; icon: typeof Upload; label: string }[] = [
    { id: "file", icon: FileSpreadsheet, label: "File Upload" },
    { id: "multiple", icon: Upload, label: "Multi-File" },
    { id: "url", icon: Globe, label: "URL / Link" },
    { id: "database", icon: Database, label: "Database" },
  ];

  return (
    <div className="max-w-2xl mx-auto">
      <div className="glass rounded-2xl overflow-hidden border border-white/10">
        {/* Tab bar */}
        <div className="flex border-b border-slate-700/50">
          {tabs.map(({ id, icon: Icon, label }) => (
            <button
              key={id}
              onClick={() => { setTab(id); setFiles([]); }}
              className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-all ${
                tab === id
                  ? "text-indigo-400 border-b-2 border-indigo-500 bg-indigo-950/30"
                  : "text-slate-500 hover:text-slate-300"
              }`}
            >
              <Icon className="w-4 h-4" />
              <span className="hidden sm:inline">{label}</span>
            </button>
          ))}
        </div>

        <div className="p-6">
          <AnimatePresence mode="wait">
            {/* File Upload */}
            {(tab === "file" || tab === "multiple") && (
              <motion.div key="file" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <div
                  {...getRootProps()}
                  className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-all ${
                    isDragActive
                      ? "border-indigo-400 bg-indigo-950/40"
                      : files.length
                      ? "border-emerald-500/50 bg-emerald-950/20"
                      : "border-slate-600 hover:border-indigo-500/60 hover:bg-slate-800/30"
                  }`}
                >
                  <input {...getInputProps()} />
                  {files.length ? (
                    <div className="space-y-2">
                      <CheckCircle className="w-10 h-10 text-emerald-400 mx-auto mb-3" />
                      {files.map((f, i) => (
                        <div key={i} className="flex items-center gap-2 text-sm text-slate-300 bg-slate-800/50 px-3 py-2 rounded-lg">
                          <FileSpreadsheet className="w-4 h-4 text-emerald-400 shrink-0" />
                          <span className="truncate">{f.name}</span>
                          <span className="ml-auto text-slate-500 shrink-0">{(f.size / 1024).toFixed(0)} KB</span>
                        </div>
                      ))}
                      <button onClick={(e) => { e.stopPropagation(); setFiles([]); }} className="text-xs text-slate-500 hover:text-red-400 mt-2 flex items-center gap-1 mx-auto">
                        <X className="w-3 h-3" /> Clear
                      </button>
                    </div>
                  ) : (
                    <>
                      <Upload className={`w-10 h-10 mx-auto mb-3 ${isDragActive ? "text-indigo-400" : "text-slate-500"}`} />
                      <p className="text-slate-300 font-medium mb-1">
                        {isDragActive ? "Drop your file here" : tab === "multiple" ? "Upload multiple files" : "Drop your dataset here"}
                      </p>
                      <p className="text-slate-500 text-sm">
                        CSV, Excel, JSON, PDF, Word, XML · Up to 200 MB
                      </p>
                    </>
                  )}
                </div>
              </motion.div>
            )}

            {/* URL */}
            {tab === "url" && (
              <motion.div key="url" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
                <div>
                  <label className="text-sm text-slate-400 mb-2 block">Data Source Type</label>
                  <select
                    value={sourceType}
                    onChange={(e) => setSourceType(e.target.value)}
                    className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="url">Public URL (CSV/Excel/JSON)</option>
                    <option value="kaggle">Kaggle Dataset URL</option>
                    <option value="github">GitHub Raw File URL</option>
                    <option value="google_sheets">Google Sheets URL</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm text-slate-400 mb-2 block">Dataset URL</label>
                  <div className="relative">
                    <Link className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                    <input
                      type="url"
                      value={url}
                      onChange={(e) => setUrl(e.target.value)}
                      placeholder="https://example.com/data.csv"
                      className="w-full bg-slate-800 border border-slate-600 rounded-lg pl-9 pr-4 py-3 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500"
                    />
                  </div>
                  <p className="text-xs text-slate-600 mt-1">Supports direct download URLs, Google Sheets share links, GitHub raw URLs</p>
                </div>
              </motion.div>
            )}

            {/* Database */}
            {tab === "database" && (
              <motion.div key="db" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-4">
                <div>
                  <label className="text-sm text-slate-400 mb-2 block">Connection String</label>
                  <input
                    value={connString}
                    onChange={(e) => setConnString(e.target.value)}
                    placeholder="postgresql://user:pass@host:5432/dbname"
                    className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-3 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 font-mono"
                  />
                  <p className="text-xs text-slate-600 mt-1">Supports PostgreSQL, MySQL, SQLite, MongoDB, MSSQL</p>
                </div>
                <div>
                  <label className="text-sm text-slate-400 mb-2 block">SQL Query</label>
                  <textarea
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    rows={3}
                    className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:border-indigo-500 font-mono resize-none"
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* CTA Button */}
          <motion.button
            onClick={handleAnalyze}
            disabled={loading}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="mt-6 w-full bg-gradient-to-r from-indigo-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-4 rounded-xl flex items-center justify-center gap-3 transition-all shadow-lg shadow-indigo-500/20"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Starting AI Pipeline...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Generate Dashboard
                <ChevronRight className="w-5 h-5 ml-auto" />
              </>
            )}
          </motion.button>

          <p className="text-center text-xs text-slate-600 mt-3">
            6 AI agents · Auto domain detection · McKinsey-grade output
          </p>
        </div>
      </div>
    </div>
  );
}

