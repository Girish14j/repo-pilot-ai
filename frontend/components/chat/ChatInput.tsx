"use client";

import { useState, KeyboardEvent } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  disabled: boolean;
}

export default function ChatInput({ onSend, isLoading, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");

  const handleSend = () => {
    if (!value.trim() || isLoading || disabled) return;
    onSend(value.trim());
    setValue("");
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    // Send on Enter, new line on Shift+Enter
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex gap-2 p-4 border-t border-zinc-800">
      <Input
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask anything about this repository..."
        disabled={isLoading || disabled}
        className="bg-zinc-900 border-zinc-700 text-white placeholder:text-zinc-500"
      />
      <Button
        onClick={handleSend}
        disabled={isLoading || disabled || !value.trim()}
        className="bg-blue-600 hover:bg-blue-500 text-white shrink-0"
      >
        {isLoading ? "..." : "Send"}
      </Button>
    </div>
  );
}