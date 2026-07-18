"use client";

import { motion } from "framer-motion";
import { FullReport } from "@/lib/types";

interface SecurityTabProps {
  report: FullReport;
}

export default function SecurityTab({ report }: SecurityTabProps) {
  const security = report.analysis.security;

  if (!security) {
    return (
      <p className="text-zinc-500 text-sm">Security analysis not available.</p>
    );
  }

  return (
    <div className="space-y-4">

      {security.critical_fixes.length > 0 && (
        <div className="border border-red-500/20 bg-red-500/10 rounded-2xl p-5">
          <h3 className="text-red-400 font-semibold mb-3">
            🚨 Critical Fixes Required
          </h3>
          <ul className="space-y-2">
            {security.critical_fixes.map((fix, i) => (
              <motion.li key={i} initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: i * 0.1 }}
                className="text-red-300 text-sm flex items-start gap-2">
                <span className="text-red-500 mt-0.5">•</span>{fix}
              </motion.li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card-glow bg-white/3 border border-white/8 rounded-2xl p-5">
          <h3 className="text-white font-semibold mb-3">OWASP Concerns</h3>
          {security.owasp_concerns.length > 0 ? (
            <ul className="space-y-2">
              {security.owasp_concerns.map((concern, i) => (
                <li key={i} className="text-yellow-400 text-sm flex items-start gap-2">
                  <span className="text-yellow-600 mt-0.5">⚠</span>{concern}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-green-400 text-sm">No OWASP concerns detected.</p>
          )}
        </div>

        <div className="card-glow bg-white/3 border border-white/8 rounded-2xl p-5">
          <h3 className="text-white font-semibold mb-3">Good Security Practices</h3>
          {security.good_practices.length > 0 ? (
            <ul className="space-y-2">
              {security.good_practices.map((practice, i) => (
                <li key={i} className="text-green-400 text-sm flex items-start gap-2">
                  <span className="mt-0.5">✓</span>{practice}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500 text-sm">None detected.</p>
          )}
        </div>
      </div>

      <div className="card-glow bg-white/3 border border-white/8 rounded-2xl p-5">
        <h3 className="text-white font-semibold mb-2">Summary</h3>
        <p className="text-gray-400 text-sm">{security.summary}</p>
      </div>
    </div>
  );
}