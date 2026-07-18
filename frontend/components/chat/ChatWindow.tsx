"use client";

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import ChatMessage from "./ChatMessage";
import ChatInput from "./ChatInput";
import { FullReport } from "@/lib/types";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface ChatWindowProps {
  report: FullReport;
  threadId: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Suggested questions to help users get started
const SUGGESTED_QUESTIONS = [
  "What are the biggest security risks in this repo?",
  "Write me a cover letter for this project",
  "Explain the architecture in simple terms",
  "What should I fix first?",
  "Give me 3 more resume bullets",
];

export default function ChatWindow({ report, threadId }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const initializedRef = useRef(false);

  // Initialize chat session when component mounts
  useEffect(() => {
    if (initializedRef.current) return;
    initializedRef.current = true;
    initializeChat();
  }, [threadId]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const initializeChat = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/github/chat/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          thread_id: threadId,
          repo_context: report,
        }),
      });

      if (!response.ok) throw new Error("Failed to initialize chat");

      setIsReady(true);

      // Add welcome message
      setMessages([{
        role: "assistant",
        content: `I've analyzed **${report.repository.full_name}** and I'm ready to answer your questions. 

The repository scored **${report.scores.overall}/10** overall. Ask me anything about the architecture, security, performance, or how to present this project on your resume.`,
      }]);

    } catch (err) {
      setError("Failed to initialize chat. Please try again.");
    }
  };

  const handleSend = async (message: string) => {
    if (!isReady || isLoading) return;

    // Immediately show user message
    const userMessage: Message = { role: "user", content: message };
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/github/chat/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          thread_id: threadId,
          message,
        }),
      });

      if (!response.ok) throw new Error("Failed to get response");

      const data = await response.json();

      // Append AI response
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.response },
      ]);

    } catch (err) {
      setError("Failed to get response. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="w-full max-w-4xl mt-8 bg-zinc-950 border border-zinc-800 rounded-2xl overflow-hidden"
    >
      {/* Header */}
      <div className="px-5 py-4 border-b border-zinc-800 flex items-center gap-3">
        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
        <h3 className="text-white font-semibold">
          Chat with {report.repository.full_name}
        </h3>
        <span className="text-zinc-600 text-xs ml-auto">
          Powered by LangGraph Memory
        </span>
      </div>

      {/* Messages */}
      <div className="h-96 overflow-y-auto p-4 space-y-4">
        {!isReady && (
          <div className="flex items-center justify-center h-full">
            <p className="text-zinc-500 text-sm">Initializing chat...</p>
          </div>
        )}

        {messages.map((msg, i) => (
          <ChatMessage
            key={i}
            role={msg.role}
            content={msg.content}
            index={i}
          />
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-zinc-800 border border-zinc-700 rounded-2xl rounded-bl-sm px-4 py-3">
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-1.5 h-1.5 bg-zinc-500 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}

        {error && (
          <p className="text-red-400 text-xs text-center">{error}</p>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Suggested questions — shown only when no user messages yet */}
      {messages.length <= 1 && isReady && (
        <div className="px-4 pb-3 flex flex-wrap gap-2">
          {SUGGESTED_QUESTIONS.map((q) => (
            <button
              key={q}
              onClick={() => handleSend(q)}
              className="text-xs px-3 py-1.5 bg-zinc-900 border border-zinc-700 rounded-full text-zinc-400 hover:text-white hover:border-zinc-500 transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Input */}
      <ChatInput
        onSend={handleSend}
        isLoading={isLoading}
        disabled={!isReady}
      />
    </motion.div>
  );
}