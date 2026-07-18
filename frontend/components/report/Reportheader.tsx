"use client";

import { motion } from "framer-motion";
import { Badge } from "@/components/ui/badge";
import ScoreCard from "./ScoreCard";
import { FullReport } from "@/lib/types";

interface ReportHeaderProps {
  report: FullReport;
}

export default function ReportHeader({ report }: ReportHeaderProps) {
  const { repository, scores, meta } = report;

  const overallColor =
    scores.overall >= 8
      ? "text-green-400"
      : scores.overall >= 6
      ? "text-yellow-400"
      : "text-red-400";

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="w-full max-w-4xl"
    >
      {/* Repo name + overall score */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-white">
            {repository.full_name}
          </h2>
          {repository.description && (
            <p className="text-zinc-400 mt-1 text-sm max-w-xl">
              {repository.description}
            </p>
          )}
          <div className="flex items-center gap-3 mt-3">
            <span className="text-zinc-500 text-sm">
              ⭐ {repository.stars.toLocaleString()}
            </span>
            <span className="text-zinc-500 text-sm">
              🍴 {repository.forks.toLocaleString()}
            </span>
            {repository.language && (
              <Badge variant="outline" className="text-zinc-400 border-zinc-700 text-xs">
                {repository.language}
              </Badge>
            )}
            {repository.topics.slice(0, 3).map((topic) => (
              <Badge
                key={topic}
                variant="outline"
                className="text-blue-400 border-blue-900 text-xs"
              >
                {topic}
              </Badge>
            ))}
          </div>
        </div>

        {/* Big overall score */}
        <div className="text-center bg-zinc-900 border border-zinc-800 rounded-2xl px-6 py-4">
          <p className="text-zinc-500 text-xs mb-1 uppercase tracking-wide">
            Overall
          </p>
          <p className={`text-4xl font-bold ${overallColor}`}>
            {scores.overall}
          </p>
          <p className="text-zinc-600 text-xs">/10</p>
        </div>
      </div>

      {/* Score breakdown grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <ScoreCard label="Architecture" score={scores.architecture} index={0} />
        <ScoreCard label="Documentation" score={scores.documentation} index={1} />
        <ScoreCard label="Security" score={scores.security} index={2} />
        <ScoreCard label="Performance" score={scores.performance} index={3} />
      </div>

      {/* Meta info */}
      <p className="text-zinc-600 text-xs">
        {meta.total_agents_run} agents completed
        {meta.errors.length > 0 && (
          <span className="text-red-500 ml-2">
            · {meta.errors.length} error(s)
          </span>
        )}
      </p>
    </motion.div>
  );
}