"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { User, Bot, ChevronDown, ExternalLink, Copy, Check } from "lucide-react";
import type { ChatMessage, EvidenceItem } from "@/types/api";
import { useUIStore } from "@/lib/store";

function MarkdownContent({ content }: { content: string }) {
  const parts = content.split(/(```[\s\S]*?```)/g);
  return (
    <div className="prose-custom">
      {parts.map((part, i) => {
        if (part.startsWith("```") && part.endsWith("```")) {
          const code = part.slice(3, -3);
          const firstLineEnd = code.indexOf("\n");
          const lang = firstLineEnd > 0 ? code.slice(0, firstLineEnd).trim() : "";
          const codeContent = firstLineEnd > 0 ? code.slice(firstLineEnd + 1) : code;
          return (
            <div key={i} className="relative group my-3">
              {lang && (
                <div className="text-xs text-text-tertiary px-3 py-1 border-b border-border">
                  {lang}
                </div>
              )}
              <pre className="!mt-0 rounded-t-none">
                <code>{codeContent}</code>
              </pre>
            </div>
          );
        }
        // Simple inline markdown
        const formatted = part
          .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
          .replace(/\*(.*?)\*/g, "<em>$1</em>")
          .replace(/`([^`]+)`/g, "<code>$1</code>")
          .replace(/\n/g, "<br/>");
        return <span key={i} dangerouslySetInnerHTML={{ __html: formatted }} />;
      })}
    </div>
  );
}

function StreamingIndicator() {
  return (
    <span className="inline-flex items-center gap-1 ml-1">
      <motion.span
        animate={{ opacity: [0, 1, 0] }}
        transition={{ duration: 1.4, repeat: Infinity, delay: 0 }}
        className="w-1.5 h-1.5 rounded-full bg-gold-400"
      />
      <motion.span
        animate={{ opacity: [0, 1, 0] }}
        transition={{ duration: 1.4, repeat: Infinity, delay: 0.2 }}
        className="w-1.5 h-1.5 rounded-full bg-gold-400"
      />
      <motion.span
        animate={{ opacity: [0, 1, 0] }}
        transition={{ duration: 1.4, repeat: Infinity, delay: 0.4 }}
        className="w-1.5 h-1.5 rounded-full bg-gold-400"
      />
    </span>
  );
}

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
  sources?: EvidenceItem[];
}

export function MessageBubble({ message, isStreaming, sources }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const { openEvidence } = useUIStore();
  const isUser = message.role === "user";

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex gap-4 ${isUser ? "flex-row-reverse" : ""}`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser
            ? "bg-gold-500/20 text-gold-400"
            : "bg-gradient-to-br from-gold-400 to-gold-600 text-surface"
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Content */}
      <div className={`flex-1 max-w-[85%] ${isUser ? "flex flex-col items-end" : ""}`}>
        <div
          className={`rounded-2xl px-5 py-3.5 ${
            isUser
              ? "bg-gold-500/10 border border-gold-500/20"
              : "glass"
          }`}
        >
          {isUser ? (
            <p className="text-sm leading-relaxed">{message.content}</p>
          ) : (
            <>
              <MarkdownContent content={message.content} />
              {isStreaming && <StreamingIndicator />}
            </>
          )}
        </div>

        {/* Actions */}
        <div className={`flex items-center gap-2 mt-1.5 ${isUser ? "justify-end" : ""}`}>
          <button
            onClick={handleCopy}
            className="p-1 rounded text-text-tertiary hover:text-text-primary hover:bg-white/5 transition-all"
            title="Copy message"
          >
            {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          </button>

          {/* Sources toggle */}
          {sources && sources.length > 0 && (
            <button
              onClick={() => setShowSources(!showSources)}
              className="flex items-center gap-1 px-2 py-1 rounded text-xs text-gold-400 hover:bg-gold-500/10 transition-all"
            >
              <ExternalLink className="h-3 w-3" />
              {sources.length} source{sources.length > 1 ? "s" : ""}
              <ChevronDown
                className={`h-3 w-3 transition-transform ${showSources ? "rotate-180" : ""}`}
              />
            </button>
          )}
        </div>

        {/* Sources panel */}
        {showSources && sources && sources.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="mt-2 space-y-2"
          >
            {sources.map((source, i) => (
              <button
                key={i}
                onClick={() => openEvidence(source)}
                className="w-full text-left glass rounded-xl p-3 hover:bg-white/[0.04] transition-all group"
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs font-medium text-gold-400">
                    {source.scripture || "Source"} · Score: {(source.score * 100).toFixed(0)}%
                  </span>
                  <span className="text-xs text-text-tertiary">{source.level}</span>
                </div>
                <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed">
                  {source.text}
                </p>
              </button>
            ))}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
