"use client";

import { motion } from "framer-motion";

interface ScoreCardProps {
  label: string;
  score: number;
  index: number; // for staggered animation
}

function getScoreColor(score: number): string {
  if (score >= 8) return "text-green-400";
  if (score >= 6) return "text-yellow-400";
  return "text-red-400";
}

function getBarColor(score: number): string {
  if (score >= 8) return "bg-green-500";
  if (score >= 6) return "bg-yellow-500";
  return "bg-red-500";
}

function getLabel(score: number): string {
  if (score >= 8) return "Excellent";
  if (score >= 6) return "Good";
  if (score >= 4) return "Fair";
  return "Needs Work";
}

export default function ScoreCard({ label, score, index }: ScoreCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.4 }}
      className="bg-zinc-900 border border-zinc-800 rounded-xl p-4"
    >
      <div className="flex justify-between items-center mb-3">
        <span className="text-zinc-400 text-sm font-medium">{label}</span>
        <div className="flex items-center gap-2">
          <span className={`text-lg font-bold ${getScoreColor(score)}`}>
            {score}
            <span className="text-zinc-600 text-sm font-normal">/10</span>
          </span>
          <span className={`text-xs ${getScoreColor(score)}`}>
            {getLabel(score)}
          </span>
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${getBarColor(score)}`}
          initial={{ width: 0 }}
          animate={{ width: `${score * 10}%` }}
          transition={{ delay: index * 0.1 + 0.3, duration: 0.6, ease: "easeOut" }}
        />
      </div>
    </motion.div>
  );
}