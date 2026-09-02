"use client";

import { motion } from "framer-motion";
import { FullReport } from "@/lib/types";

interface CodeTabProps {
  report: FullReport;
}

const severityColor = {
  critical: "text-red-400 bg-red-950/30 border-red-900",
  warning: "text-yellow-400 bg-yellow-950/30 border-yellow-900",
  suggestion: "text-blue-400 bg-blue-950/30 border-blue-900",
};

const effortColor = {
  low: "text-green-400 border-green-900",
  medium: "text-yellow-400 border-yellow-900",
  high: "text-red-400 border-red-900",
};

export default function CodeTab({ report }: CodeTabProps) {
  const codeQuality = report.analysis.code_quality;
  const optimization = report.analysis.optimization;

  if (!codeQuality && !optimization) {
    return (
      <p className="text-zinc-500 text-sm">
        Code analysis not available for this repository.
      </p>
    );
  }

  return (
    <div className="space-y-6">

      {/* Code Quality Issues */}
      {codeQuality && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-white font-semibold">
              🔬 Code Issues ({codeQuality.issues?.length || 0} found)
            </h3>
            <span className="text-zinc-400 text-sm">
              Score: {codeQuality.score}/10
            </span>
          </div>

          {/* Overall assessment */}
          <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
            <p className="text-zinc-400 text-sm">
              {codeQuality.overall_assessment}
            </p>
          </div>

          {/* Top 3 fixes */}
          {codeQuality.top_3_fixes?.length > 0 && (
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
              <h4 className="text-white text-sm font-medium mb-3">
                🎯 Top Priority Fixes
              </h4>
              <ol className="space-y-2">
                {codeQuality.top_3_fixes.map((fix: string, i: number) => (
                  <li key={i} className="text-zinc-400 text-sm flex gap-2">
                    <span className="text-blue-500 font-mono shrink-0">
                      {i + 1}.
                    </span>
                    {fix}
                  </li>
                ))}
              </ol>
            </div>
          )}

          {/* Individual issues */}
          <div className="space-y-3">
            {codeQuality.issues?.map((issue: any, i: number) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className={`border rounded-xl p-4 ${severityColor[issue.severity as keyof typeof severityColor] || severityColor.suggestion}`}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span className="font-mono text-xs opacity-70">
                    {issue.file}
                  </span>
                  <span className="text-xs uppercase font-medium opacity-70 shrink-0">
                    {issue.severity}
                  </span>
                </div>
                <p className="text-sm mb-2">{issue.issue}</p>
                <div className="border-t border-current/20 pt-2 mt-2">
                  <p className="text-xs opacity-70">
                    <span className="font-medium">Fix: </span>
                    {issue.fix}
                  </p>
                </div>
              </motion.div>
            ))}
          </div>

          {/* Good patterns */}
          {codeQuality.good_patterns?.length > 0 && (
            <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4">
              <h4 className="text-white text-sm font-medium mb-3">
                ✅ Good Patterns Detected
              </h4>
              <ul className="space-y-1">
                {codeQuality.good_patterns.map((pattern: string, i: number) => (
                  <li key={i} className="text-green-400 text-sm flex gap-2">
                    <span className="shrink-0">✓</span>
                    {pattern}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Optimization Suggestions */}
      {optimization && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-white font-semibold">
              ⚙️ Optimization Opportunities
            </h3>
            <div className="flex gap-3 text-xs text-zinc-500">
              <span>Perf: {optimization.performance_score}/10</span>
              <span>Readability: {optimization.readability_score}/10</span>
            </div>
          </div>

          {/* Quick wins */}
          {optimization.quick_wins?.length > 0 && (
            <div className="bg-green-950/20 border border-green-900 rounded-xl p-4">
              <h4 className="text-green-400 text-sm font-medium mb-3">
                ⚡ Quick Wins
              </h4>
              <ul className="space-y-1">
                {optimization.quick_wins.map((win: string, i: number) => (
                  <li key={i} className="text-green-300 text-sm flex gap-2">
                    <span className="shrink-0">→</span>
                    {win}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Individual suggestions */}
          <div className="space-y-3">
            {optimization.suggestions?.map((s: any, i: number) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="bg-zinc-900 border border-zinc-800 rounded-xl p-4"
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="font-mono text-xs text-zinc-500">
                    {s.file}
                  </span>
                  <div className="flex gap-2">
                    <span className={`text-xs px-2 py-0.5 border rounded-full ${effortColor[s.effort as keyof typeof effortColor] || effortColor.medium}`}>
                      {s.effort} effort
                    </span>
                    <span className="text-xs px-2 py-0.5 border border-blue-900 text-blue-400 rounded-full">
                      {s.impact}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 mb-3">
                  <div className="bg-red-950/20 border border-red-900/50 rounded-lg p-2">
                    <p className="text-red-400 text-xs font-medium mb-1">Current</p>
                    <p className="text-red-300 text-xs font-mono">
                      {s.current_pattern}
                    </p>
                  </div>
                  <div className="bg-green-950/20 border border-green-900/50 rounded-lg p-2">
                    <p className="text-green-400 text-xs font-medium mb-1">Optimized</p>
                    <p className="text-green-300 text-xs font-mono">
                      {s.optimized_pattern}
                    </p>
                  </div>
                </div>

                <p className="text-zinc-400 text-xs">{s.explanation}</p>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}