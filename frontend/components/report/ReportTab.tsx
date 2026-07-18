"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import AnalysisTab from "./AnalysisTab";
import SecurityTab from "./SecurityTab";
import CareerTab from "./CareerTab";
import { FullReport } from "@/lib/types";

interface ReportTabsProps {
  report: FullReport;
}

const tabs = [
  { id: "analysis", label: "Analysis" },
  { id: "security", label: "Security" },
  { id: "career", label: "Career" },
];

export default function ReportTabs({ report }: ReportTabsProps) {
  const [activeTab, setActiveTab] = useState("analysis");

  return (
    <div className="w-full mt-6">

      {/* Tab navigation */}
      <div className="flex gap-1 mb-6 bg-white/3 border border-white/8 rounded-xl p-1 w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`relative px-5 py-2 text-sm font-semibold rounded-lg transition-colors ${
              activeTab === tab.id
                ? "text-white"
                : "text-gray-500 hover:text-gray-300"
            }`}
          >
            {/* Animated background for active tab */}
            {activeTab === tab.id && (
              <motion.div
                layoutId="activeTab"
                className="absolute inset-0 bg-indigo-600 rounded-lg"
                transition={{ duration: 0.2 }}
              />
            )}
            <span className="relative z-10">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        {activeTab === "analysis" && <AnalysisTab report={report} />}
        {activeTab === "security" && <SecurityTab report={report} />}
        {activeTab === "career" && <CareerTab report={report} />}
      </motion.div>
    </div>
  );
}