"use client";

import { motion } from "framer-motion";

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  index: number;
}

export default function ChatMessage({ role, content, index }: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className={`flex ${isUser ? "justify-end" : "justify-start"}`}
    >
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? "bg-blue-600 text-white rounded-br-sm"
            : "bg-zinc-800 text-zinc-200 rounded-bl-sm border border-zinc-700"
        }`}
      >
        {/* Render content with basic markdown support */}
        {content.split("\n").map((line, i) => (
          <p key={i} className={line === "" ? "h-2" : ""}>
            {line}
          </p>
        ))}
      </div>
    </motion.div>
  );
}