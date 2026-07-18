"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { GitBranch, Sparkles, Brain, Shield, BarChart3, FileText, Zap, Loader2, XCircle, Globe, Star, GitFork, Code2, ArrowRight } from "lucide-react";
import { streamGraphAnalysis } from "../lib/api";
import { FullReport } from "../lib/types";
import ReportTabs from "@/components/report/ReportTab";
import ChatWindow from "@/components/chat/ChatWindow";

const EXAMPLE_REPOS = [
  "https://github.com/tiangolo/fastapi",
  "https://github.com/vercel/next.js",
  "https://github.com/facebook/react",
];

const FEATURES = [
  { icon: Brain,     label: "AI Code Review",  desc: "Deep analysis by LLM agents" },
  { icon: Shield,    label: "Security Scan",   desc: "OWASP-based vulnerability check" },
  { icon: BarChart3, label: "Score Breakdown", desc: "Architecture, docs, performance" },
  { icon: FileText,  label: "Career Content",  desc: "Resume bullets & LinkedIn posts" },
];

const AGENTS = [
  { key: "repository_agent",    label: "Repository",     icon: "🔍", desc: "Fetching GitHub data" },
  { key: "architecture_agent",  label: "Architecture",   icon: "🏗️", desc: "Analyzing code structure" },
  { key: "documentation_agent", label: "Documentation",  icon: "📄", desc: "Reviewing README quality" },
  { key: "security_agent",      label: "Security",       icon: "🔒", desc: "OWASP vulnerability scan" },
  { key: "performance_agent",   label: "Performance",    icon: "⚡", desc: "Identifying bottlenecks" },
  { key: "interview_agent",     label: "Interview Prep", icon: "🎤", desc: "Generating questions" },
  { key: "resume_agent",        label: "Resume",         icon: "📋", desc: "Writing bullet points" },
  { key: "final_report_agent",  label: "Final Report",   icon: "✅", desc: "Assembling results" },
];

export default function Home() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [report, setReport] = useState<FullReport | null>(null);
  const [threadId, setThreadId] = useState<string | null>(null);
  const [typedText, setTypedText] = useState("");
  const [agentResults, setAgentResults] = useState<Record<string, any>>({});
  const [activeAgent, setActiveAgent] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const placeholder = "https://github.com/owner/repo";
  useEffect(() => {
    let i = 0;
    const interval = setInterval(() => {
      setTypedText(placeholder.slice(0, i));
      i++;
      if (i > placeholder.length) clearInterval(interval);
    }, 50);
    return () => clearInterval(interval);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setReport(null);
    setThreadId(null);
    setAgentResults({});
    setActiveAgent("");
    setLoading(true);

    try {
      for await (const event of streamGraphAnalysis(url)) {
        if (event.agent === "error") {
          setError(event.error);
          break;
        }
        setActiveAgent(event.agent);
        if (event.data) {
          setAgentResults(prev => ({ ...prev, [event.agent]: event.data }));
        }
        if (event.agent === "final_report_agent" && event.data) {
          const fullReport = event.data as FullReport;
          setReport(fullReport);
          const repoName = fullReport.repository?.full_name?.replace("/", "-") ?? "repo";
          setThreadId(`${repoName}-${Date.now()}`);
        }
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
      setActiveAgent("");
    }
  }

  return (
    <div className="min-h-screen bg-[#020817] text-white relative overflow-hidden">

      {/* Background orbs */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="orb-1 absolute top-[-20%] left-[-10%] w-[600px] h-[600px] rounded-full bg-indigo-600/20 blur-[120px]" />
        <div className="orb-2 absolute top-[30%] right-[-15%] w-[500px] h-[500px] rounded-full bg-purple-600/20 blur-[120px]" />
        <div className="orb-3 absolute bottom-[-10%] left-[30%] w-[400px] h-[400px] rounded-full bg-cyan-600/15 blur-[100px]" />
        <div className="grid-bg absolute inset-0" />
      </div>

      {/* Navbar */}
      <motion.nav
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="relative z-10 flex items-center justify-between px-8 py-5 border-b border-white/5 backdrop-blur-sm"
      >
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
            <GitBranch className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-lg">RepoPilot <span className="text-indigo-400">AI</span></span>
        </div>
        <div className="flex items-center gap-6 text-sm text-gray-400">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
            API Online
          </span>
          <a href="http://localhost:8000/docs" target="_blank" className="hover:text-white transition-colors flex items-center gap-1">
            Swagger Docs <Globe className="w-3 h-3" />
          </a>
        </div>
      </motion.nav>

      <div className="relative z-10 max-w-5xl mx-auto px-6 py-16">

        {/* Hero — only shown before any analysis */}
        {!report && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/20 rounded-full px-4 py-1.5 text-sm text-indigo-300 mb-6"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Powered by LangGraph Multi-Agent AI
            </motion.div>

            <h1 className="text-6xl font-bold mb-4 leading-tight">
              Analyze any{" "}
              <span className="shimmer-text">GitHub repo</span>
              <br />in seconds
            </h1>
            <p className="text-xl text-gray-400 mb-12 max-w-2xl mx-auto">
              AI agents review your code architecture, security, documentation,
              and generate career content — all for free.
            </p>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
              {FEATURES.map(({ icon: Icon, label, desc }) => (
                <motion.div
                  key={label}
                  whileHover={{ scale: 1.03 }}
                  className="card-glow bg-white/3 border border-white/8 rounded-xl p-4 text-left"
                >
                  <Icon className="w-5 h-5 text-indigo-400 mb-2" />
                  <div className="font-semibold text-sm">{label}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{desc}</div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Input Form */}
        <motion.form
          onSubmit={handleSubmit}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mb-8"
        >
          <div className="relative flex gap-3 p-2 bg-white/5 border border-white/10 rounded-2xl backdrop-blur-sm focus-within:border-indigo-500/50 transition-colors">
            <GitBranch className="absolute left-5 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              ref={inputRef}
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder={typedText}
              className="flex-1 bg-transparent pl-12 pr-4 py-3 text-white placeholder-gray-600 focus:outline-none text-base"
              required
            />
            <motion.button
              type="submit"
              disabled={loading}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="flex items-center gap-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 disabled:cursor-not-allowed px-6 py-3 rounded-xl font-semibold text-sm transition-all"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Zap className="w-4 h-4" />}
              {loading ? "Analyzing..." : "Analyze"}
            </motion.button>
          </div>

          {!report && (
            <div className="flex items-center gap-2 mt-3 flex-wrap">
              <span className="text-xs text-gray-600">Try:</span>
              {EXAMPLE_REPOS.map((repo) => (
                <button
                  key={repo}
                  type="button"
                  onClick={() => setUrl(repo)}
                  className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
                >
                  {repo.replace("https://github.com/", "")}
                </button>
              ))}
            </div>
          )}
        </motion.form>

        {/* Error */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-3 bg-red-500/10 border border-red-500/20 text-red-300 rounded-xl px-4 py-3 mb-6 text-sm"
            >
              <XCircle className="w-4 h-4 shrink-0" />
              {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Loading — agent pipeline progress */}
        <AnimatePresence>
          {loading && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="space-y-4"
            >
              <div className="card-glow bg-white/3 border border-white/8 rounded-2xl p-6">
                <div className="flex items-center gap-3 mb-6">
                  <Brain className="w-5 h-5 text-indigo-400 animate-pulse" />
                  <span className="font-semibold">AI Agents Running...</span>
                  <span className="text-xs text-gray-500 ml-auto">
                    {Object.keys(agentResults).length} / {AGENTS.length} complete
                  </span>
                </div>
                <div className="space-y-3">
                  {AGENTS.map(({ key, label, icon, desc }) => {
                    const done    = key in agentResults;
                    const running = activeAgent === key;
                    return (
                      <motion.div
                        key={key}
                        initial={{ opacity: 0.4 }}
                        animate={{ opacity: done || running ? 1 : 0.4 }}
                        className={`flex items-center gap-3 p-3 rounded-xl transition-all ${
                          running ? "bg-indigo-500/10 border border-indigo-500/20" :
                          done    ? "bg-green-500/5 border border-green-500/10" :
                                    "border border-transparent"
                        }`}
                      >
                        <span className="text-lg w-6 text-center">{icon}</span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className={`text-sm font-medium ${
                              done ? "text-green-400" : running ? "text-indigo-300" : "text-gray-500"
                            }`}>{label}</span>
                            {running && <Loader2 className="w-3 h-3 text-indigo-400 animate-spin" />}
                            {done    && <span className="text-xs text-green-500">✓ Done</span>}
                          </div>
                          <p className="text-xs text-gray-600 truncate">{desc}</p>
                        </div>
                        {done && agentResults[key]?.score !== undefined && (
                          <span className="text-sm font-bold text-indigo-400 shrink-0">
                            {agentResults[key].score}/10
                          </span>
                        )}
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Report */}
        <AnimatePresence>
          {report && !loading && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              {/* Repo header */}
              <div className="card-glow bg-white/3 border border-white/8 rounded-2xl p-6 mb-6">
                <div className="flex items-start justify-between flex-wrap gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <GitBranch className="w-5 h-5 text-gray-400" />
                      <h2 className="text-xl font-bold">{report.repository.full_name}</h2>
                    </div>
                    <p className="text-gray-400 text-sm">{report.repository.description || "No description"}</p>
                  </div>
                  <div className="flex gap-4 text-sm text-gray-400">
                    <span className="flex items-center gap-1"><Star className="w-4 h-4 text-yellow-400" />{report.repository.stars.toLocaleString()}</span>
                    <span className="flex items-center gap-1"><GitFork className="w-4 h-4 text-blue-400" />{report.repository.forks.toLocaleString()}</span>
                    <span className="flex items-center gap-1"><Code2 className="w-4 h-4 text-green-400" />{report.repository.language}</span>
                  </div>
                </div>
              </div>

              {/* Tabs */}
              <ReportTabs report={report} />

              {/* Chat */}
              {threadId && <ChatWindow report={report} threadId={threadId} />}
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Footer */}
      <div className="relative z-10 text-center py-8 text-gray-700 text-xs border-t border-white/5">
        RepoPilot AI — Built with FastAPI, LangGraph, Next.js
      </div>
    </div>
  );
}
