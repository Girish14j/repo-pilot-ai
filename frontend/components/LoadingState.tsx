"use client";

import { motion } from "framer-motion";

const steps = [
  { label: "Fetching repository data", duration: 3000 },
  { label: "Analyzing architecture", duration: 6000 },
  { label: "Reviewing code quality", duration: 9000 },
  { label: "Generating career content", duration: 12000 },
];

export default function LoadingState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-8">

      {/* Animated spinner */}
      <motion.div
        className="w-16 h-16 rounded-full border-4 border-zinc-700 border-t-blue-500"
        animate={{ rotate: 360 }}
        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
      />

      <div className="flex flex-col gap-3 w-full max-w-sm">
        {steps.map((step, index) => (
          <motion.div
            key={step.label}
            className="flex items-center gap-3"
            // Each step fades in after the previous one
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 2, duration: 0.5 }}
          >
            <motion.div
              className="w-2 h-2 rounded-full bg-blue-500"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              transition={{ delay: index * 2, duration: 0.3 }}
            />
            <span className="text-zinc-400 text-sm">{step.label}</span>
          </motion.div>
        ))}
      </div>

      <p className="text-zinc-500 text-sm">
        This takes 20–40 seconds. The AI is reading your repository.
      </p>
    </div>
  );
}