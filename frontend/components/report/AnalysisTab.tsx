"use client";

import { motion } from "framer-motion";
import { FullReport } from "@/lib/types";

interface AnalysisTabProps {
  report: FullReport;
}

function Section({
  title,
  items,
  color = "zinc",
}: {
  title: string;
  items: string[];
  color?: "green" | "red" | "yellow" | "blue" | "zinc";
}) {
  if (!items || items.length === 0) return null;

  const dotColor = {
    green: "bg-green-500",
    red: "bg-red-500",
    yellow: "bg-yellow-500",
    blue: "bg-blue-500",
    zinc: "bg-zinc-500",
  }[color];

  return (
    <div className="mb-4">
      <h4 className="text-gray-400 text-xs font-semibold mb-2 uppercase tracking-wider">
        {title}
      </h4>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <motion.li
            key={i}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            className="flex items-start gap-2 text-sm text-gray-400"
          >
            <span className={`w-1.5 h-1.5 rounded-full ${dotColor} mt-1.5 shrink-0`} />
            {item}
          </motion.li>
        ))}
      </ul>
    </div>
  );
}

export default function AnalysisTab({ report }: AnalysisTabProps) {
  const { architecture, documentation, performance, refactoring } = report.analysis;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

      {/* Architecture */}
      {architecture && (
        <div className="card-glow bg-white/3 border border-white/8 rounded-2xl p-5">
          <h3 className="text-white font-semibold mb-3">🏗️ Architecture</h3>
          <p className="text-gray-400 text-sm mb-4">{architecture.summary}</p>
          <Section title="Patterns Detected" items={architecture.patterns_detected} color="blue" />
          <Section title="Strengths" items={architecture.strengths} color="green" />
          <Section title="Violations" items={architecture.violations} color="red" />
          <Section title="Recommendations" items={architecture.recommendations} color="yellow" />
        </div>
      )}

      {/* Documentation */}
      {documentation && (
        <div className="card-glow bg-white/3 border border-white/8 rounded-2xl p-5">
          <h3 className="text-white font-semibold mb-3">📝 Documentation</h3>
          <p className="text-gray-400 text-sm mb-4">{documentation.summary}</p>
          <Section title="Strengths" items={documentation.strengths} color="green" />
          <Section title="Missing Sections" items={documentation.missing_sections} color="red" />
          <Section title="Improvements" items={documentation.improvements} color="yellow" />
        </div>
      )}

      {/* Performance */}
      {performance && (
        <div className="card-glow bg-white/3 border border-white/8 rounded-2xl p-5">
          <h3 className="text-white font-semibold mb-3">⚡ Performance</h3>
          <p className="text-gray-400 text-sm mb-4">{performance.summary}</p>
          <Section title="Good Practices" items={performance.good_practices} color="green" />
          <Section title="Potential Bottlenecks" items={performance.potential_bottlenecks} color="red" />
          <Section title="Recommendations" items={performance.recommendations} color="yellow" />
        </div>
      )}

      {/* Refactoring */}
      {refactoring && (
        <div className="card-glow bg-white/3 border border-white/8 rounded-2xl p-5">
          <h3 className="text-white font-semibold mb-3">🔧 Refactoring</h3>
          <p className="text-gray-400 text-sm mb-4">{refactoring.summary}</p>
          <Section title="Priority Refactors" items={refactoring.priority_refactors} color="red" />
          <Section title="Quick Wins" items={refactoring.quick_wins} color="green" />
          <Section title="Long-term Improvements" items={refactoring.long_term_improvements} color="blue" />
          <div className="mt-4 p-3 bg-white/5 rounded-xl">
            <p className="text-gray-400 text-xs">
              <span className="text-gray-300 font-medium">Estimated Impact: </span>
              {refactoring.estimated_impact}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}