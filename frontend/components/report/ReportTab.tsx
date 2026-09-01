"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import AnalysisTab from "./AnalysisTab";
import SecurityTab from "./SecurityTab";
import CareerTab from "./CareerTab";
import CodeTab from "./CodeTab";      
import { FullReport } from "@/lib/types";

interface ReportTabsProps {
  report: FullReport;
}

const tabs = [
  { id: "analysis", label: "Analysis" },
  { id: "code", label: "Code Review" },    // ← NEW
  { id: "security", label: "Security" },
  { id: "career", label: "Career" },
];

export default function ReportTabs({ report }: ReportTabsProps) {
  const [activeTab, setActiveTab] = useState("analysis");

  return (
    <div className="w-full max-w-4xl mt-8">
      <div className="flex gap-1 mb-6 bg-zinc-900 border border-zinc-800 rounded-lg p-1 w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`relative px-4 py-2 text-sm font-medium rounded-md transition-colors ${
              activeTab === tab.id
                ? "text-white"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            {activeTab === tab.id && (
              <motion.div
                layoutId="activeTab"
                className="absolute inset-0 bg-zinc-700 rounded-md"
                transition={{ duration: 0.2 }}
              />
            )}
            <span className="relative z-10">{tab.label}</span>
          </button>
        ))}
      </div>

      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        {activeTab === "analysis" && <AnalysisTab report={report} />}
        {activeTab === "code" && <CodeTab report={report} />}       {/* ← NEW */}
        {activeTab === "security" && <SecurityTab report={report} />}
        {activeTab === "career" && <CareerTab report={report} />}
      </motion.div>
    </div>
  );
}