"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { FullReport } from "@/lib/types";

interface CareerTabProps {
  report: FullReport;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Button
      onClick={handleCopy}
      variant="outline"
      size="sm"
      className="text-xs border-white/20 text-gray-400 hover:text-white hover:border-white/40 bg-transparent"
    >
      {copied ? "✓ Copied" : "Copy"}
    </Button>
  );
}

export default function CareerTab({ report }: CareerTabProps) {
  const { interview, resume } = report.career;

  return (
    <div className="space-y-4">

      {resume && (
        <>
          <div className="card-glow bg-white/3 border border-white/8 rounded-2xl p-5">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-white font-semibold">📄 Resume Bullets</h3>
              <CopyButton text={resume.resume_bullets.join("\n")} />
            </div>
            <ul className="space-y-2">
              {resume.resume_bullets.map((bullet, i) => (
                <motion.li key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.08 }}
                  className="text-gray-300 text-sm flex items-start gap-2">
                  <span className="text-indigo-400 mt-0.5 shrink-0">•</span>{bullet}
                </motion.li>
              ))}
            </ul>
          </div>

          <div className="card-glow bg-white/3 border border-white/8 rounded-2xl p-5">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-white font-semibold">📋 ATS Project Description</h3>
              <CopyButton text={resume.ats_description} />
            </div>
            <p className="text-gray-400 text-sm leading-relaxed">{resume.ats_description}</p>
          </div>

          <div className="card-glow bg-white/3 border border-white/8 rounded-2xl p-5">
            <h3 className="text-white font-semibold mb-4">🛠️ Skills Demonstrated</h3>
            <div className="flex flex-wrap gap-2">
              {resume.skills_demonstrated.map((skill, i) => (
                <span key={i} className="px-2 py-1 bg-indigo-500/10 border border-indigo-500/30 rounded-lg text-indigo-300 text-xs">{skill}</span>
              ))}
            </div>
          </div>

          <div className="card-glow bg-white/3 border border-white/8 rounded-2xl p-5">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-white font-semibold">💼 LinkedIn Post</h3>
              <CopyButton text={resume.linkedin_post} />
            </div>
            <p className="text-gray-400 text-sm leading-relaxed whitespace-pre-line">{resume.linkedin_post}</p>
          </div>
        </>
      )}

      {interview && (
        <>
          <div className="card-glow bg-white/3 border border-white/8 rounded-2xl p-5">
            <h3 className="text-white font-semibold mb-4">🎯 Technical Questions</h3>
            <ol className="space-y-3">
              {interview.technical_questions.map((q, i) => (
                <li key={i} className="text-gray-400 text-sm flex items-start gap-3">
                  <span className="text-indigo-400 font-mono text-xs mt-0.5 shrink-0">{String(i + 1).padStart(2, "0")}</span>{q}
                </li>
              ))}
            </ol>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="card-glow bg-white/3 border border-white/8 rounded-2xl p-5">
              <h3 className="text-white font-semibold mb-4">💬 Behavioral Questions</h3>
              <ol className="space-y-3">
                {interview.behavioral_questions.map((q, i) => (
                  <li key={i} className="text-gray-400 text-sm flex items-start gap-2">
                    <span className="text-purple-400 mt-0.5 shrink-0">•</span>{q}
                  </li>
                ))}
              </ol>
            </div>
            <div className="card-glow bg-white/3 border border-white/8 rounded-2xl p-5">
              <h3 className="text-white font-semibold mb-4">🏗️ System Design Questions</h3>
              <ol className="space-y-3">
                {interview.system_design_questions.map((q, i) => (
                  <li key={i} className="text-gray-400 text-sm flex items-start gap-2">
                    <span className="text-green-400 mt-0.5 shrink-0">•</span>{q}
                  </li>
                ))}
              </ol>
            </div>
          </div>

          <div className="card-glow bg-white/3 border border-white/8 rounded-2xl p-5">
            <h3 className="text-white font-semibold mb-4">📚 Topics to Study</h3>
            <div className="flex flex-wrap gap-2">
              {interview.topics_to_study.map((topic, i) => (
                <span key={i} className="px-2 py-1 bg-purple-500/10 border border-purple-500/30 rounded-lg text-purple-300 text-xs">{topic}</span>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}