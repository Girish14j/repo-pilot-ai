"use client";

import { useState } from "react";
import { fetchFullReport } from "../lib/api";

type Tab = "review" | "assistant";

export default function Home() {
  const [url, setUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [data, setData] = useState<any>(null);
  const [tab, setTab] = useState<Tab>("review");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setData(null);
    setLoading(true);
    try {
      const result = await fetchFullReport(url);
      setData(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-gray-950 text-white p-8">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-bold mb-2">🚀 RepoPilot AI</h1>
        <p className="text-gray-400 mb-8">AI-powered GitHub repository reviewer & career assistant</p>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="flex gap-3 mb-8">
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://github.com/owner/repo"
            className="flex-1 bg-gray-900 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-900 disabled:cursor-not-allowed px-6 py-3 rounded-lg font-semibold transition-colors"
          >
            {loading ? "Analyzing..." : "Analyze"}
          </button>
        </form>

        {/* Error */}
        {error && (
          <div className="bg-red-900/50 border border-red-700 text-red-300 rounded-lg px-4 py-3 mb-6">
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="text-center text-gray-400 py-16">
            <div className="text-5xl mb-4 animate-spin inline-block">⚙️</div>
            <p>Fetching repo & running AI analysis... this may take ~30s</p>
          </div>
        )}

        {/* Results */}
        {data && (
          <div>
            {/* Repo Header */}
            <div className="bg-gray-900 rounded-xl p-5 mb-6">
              <h2 className="text-xl font-bold">{data.repo.full_name}</h2>
              <p className="text-gray-400 mt-1">{data.repo.description || "No description"}</p>
              <div className="flex gap-4 mt-3 text-sm text-gray-400">
                <span>⭐ {data.repo.stars}</span>
                <span>🍴 {data.repo.forks}</span>
                <span>💻 {data.repo.language}</span>
              </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 mb-6">
              <button
                onClick={() => setTab("review")}
                className={`px-5 py-2 rounded-lg font-semibold transition-colors ${tab === "review" ? "bg-blue-600" : "bg-gray-800 hover:bg-gray-700"}`}
              >
                Code Review
              </button>
              <button
                onClick={() => setTab("assistant")}
                className={`px-5 py-2 rounded-lg font-semibold transition-colors ${tab === "assistant" ? "bg-purple-600" : "bg-gray-800 hover:bg-gray-700"}`}
              >
                Developer Assistant
              </button>
            </div>

            {/* Code Review Tab */}
            {tab === "review" && (
              <div className="space-y-5">
                <div className="bg-gray-900 rounded-xl p-5">
                  <h3 className="font-semibold text-gray-400 uppercase text-xs mb-2">Overall Score</h3>
                  <p className="text-5xl font-bold text-blue-400">{data.analysis.overall_score}<span className="text-2xl text-gray-500">/10</span></p>
                </div>

                <div className="bg-gray-900 rounded-xl p-5">
                  <h3 className="font-semibold text-gray-400 uppercase text-xs mb-3">Score Breakdown</h3>
                  <div className="grid grid-cols-2 gap-3">
                    {Object.entries(data.analysis.scores).map(([key, val]: any) => (
                      <div key={key} className="flex justify-between">
                        <span className="capitalize text-gray-300">{key.replace("_", " ")}</span>
                        <span className="font-bold text-blue-400">{val}/10</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-gray-900 rounded-xl p-5">
                  <h3 className="font-semibold text-gray-400 uppercase text-xs mb-2">Executive Summary</h3>
                  <p className="text-gray-300">{data.analysis.executive_summary}</p>
                </div>

                <Section title="✅ Strengths" items={data.analysis.strengths} color="text-green-400" />
                <Section title="⚠️ Weaknesses" items={data.analysis.weaknesses} color="text-yellow-400" />
                <Section title="🔒 Security Concerns" items={data.analysis.security_concerns} color="text-red-400" />
                <Section title="📋 Recommendations" items={data.analysis.recommendations} color="text-blue-400" />
                <Section title="📁 Missing Files" items={data.analysis.missing_files} color="text-gray-400" />

                <div className="bg-gray-900 rounded-xl p-5">
                  <h3 className="font-semibold text-gray-400 uppercase text-xs mb-2">Tech Stack</h3>
                  <p className="text-gray-300">{data.analysis.tech_stack_summary}</p>
                </div>
              </div>
            )}

            {/* Assistant Tab */}
            {tab === "assistant" && (
              <div className="space-y-5">
                <Section title="📄 Resume Bullets" items={data.assistant.resume_bullets} color="text-purple-400" />

                <div className="bg-gray-900 rounded-xl p-5">
                  <h3 className="font-semibold text-gray-400 uppercase text-xs mb-2">ATS Description</h3>
                  <p className="text-gray-300">{data.assistant.ats_description}</p>
                </div>

                <Section title="🎤 Interview Questions" items={data.assistant.interview_questions} color="text-blue-400" />
                <Section title="📝 README Improvements" items={data.assistant.readme_improvements} color="text-yellow-400" />
                <Section title="💡 Feature Suggestions" items={data.assistant.feature_suggestions} color="text-green-400" />

                <div className="bg-gray-900 rounded-xl p-5">
                  <h3 className="font-semibold text-gray-400 uppercase text-xs mb-2">LinkedIn Post</h3>
                  <p className="text-gray-300 whitespace-pre-line">{data.assistant.linkedin_post}</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}

function Section({ title, items, color }: { title: string; items: string[]; color: string }) {
  return (
    <div className="bg-gray-900 rounded-xl p-5">
      <h3 className="font-semibold text-gray-400 uppercase text-xs mb-3">{title}</h3>
      <ul className="space-y-2">
        {items.map((item, i) => (
          <li key={i} className={`${color} text-sm`}>• {item}</li>
        ))}
      </ul>
    </div>
  );
}
