"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { Send, Sparkles, StopCircle } from "lucide-react";

interface ChatInputProps {
  onSend: (message: string) => void;
  onStop: () => void;
  isStreaming: boolean;
  disabled?: boolean;
}

export function ChatInput({ onSend, onStop, isStreaming, disabled }: ChatInputProps) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = "auto";
      ta.style.height = Math.min(ta.scrollHeight, 180) + "px";
    }
  }, [input]);

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming || disabled) return;
    onSend(trimmed);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="border-t border-border p-4 bg-surface/80 backdrop-blur-sm">
      <div className="max-w-3xl mx-auto">
        <div className="relative">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about Hindu scriptures, philosophy, or concepts..."
            rows={1}
            disabled={isStreaming || disabled}
            className="w-full resize-none rounded-xl border border-border bg-surface-raised px-4 py-3 pr-20 text-sm text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-1 focus:ring-accent/20 focus:border-border-strong transition-all disabled:opacity-50"
          />

          <div className="absolute right-2 bottom-2 flex items-center gap-1">
            {isStreaming ? (
              <button
                onClick={onStop}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-50 text-red-500 text-xs font-medium hover:bg-red-100 transition-all"
              >
                <StopCircle className="h-3.5 w-3.5" />
                Stop
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={!input.trim() || disabled}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-gold-500 text-white text-xs font-semibold hover:bg-gold-400 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <Send className="h-3.5 w-3.5" />
                Send
              </button>
            )}
          </div>
        </div>

        <div className="flex items-center gap-4 mt-2 px-1">
          <div className="flex items-center gap-1.5 text-[11px] text-text-tertiary">
            <Sparkles className="h-3 w-3" />
            <span>Evidence-backed answers</span>
          </div>
          <div className="text-[11px] text-text-tertiary">·</div>
          <div className="text-[11px] text-text-tertiary">Shift+Enter for new line</div>
        </div>
      </div>
    </div>
  );
}
