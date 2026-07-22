"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  User, Bot, ChevronDown, Copy, Check,
  Sparkles, ScrollText, BookOpen, Bookmark, BookmarkCheck,
} from "lucide-react";
import type { ChatMessage, EvidenceItem } from "@/types/api";
import { useUIStore, useBookmarkStore } from "@/lib/store";

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
                <div className="text-[11px] text-text-tertiary px-3 py-1.5 border-b border-border bg-warm-50 rounded-t-xl">
                  {lang}
                </div>
              )}
              <pre className="!mt-0 rounded-t-none">
                <code>{codeContent}</code>
              </pre>
            </div>
          );
        }
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
    <motion.span
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="inline-flex items-center gap-1 ml-1"
    >
      {[0, 0.2, 0.4].map((delay, i) => (
        <motion.span
          key={i}
          animate={{ opacity: [0.2, 1, 0.2] }}
          transition={{ duration: 1.2, repeat: Infinity, delay }}
          className="w-1.5 h-1.5 rounded-full bg-gold-400"
        />
      ))}
    </motion.span>
  );
}

function ThinkingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-2.5 px-3 py-2 rounded-xl glass max-w-fit"
    >
      <div className="flex items-center gap-0.5">
        {[0, 0.15, 0.3].map((delay, i) => (
          <motion.div
            key={i}
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 1, repeat: Infinity, delay }}
            className="w-1 h-1 rounded-full bg-gold-400/50"
          />
        ))}
      </div>
      <span className="text-[11px] text-text-secondary font-medium">
        Consulting the knowledge base
      </span>
      <BookOpen className="h-3 w-3 text-text-tertiary" />
    </motion.div>
  );
}

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
  isThinking?: boolean;
  sources?: EvidenceItem[];
}

export function MessageBubble({ message, isStreaming, isThinking, sources }: MessageBubbleProps) {
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
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center ring-1 ring-white/10 ${
          isUser
            ? "bg-accent-subtle text-gold-600"
            : "bg-gradient-to-br from-gold-500 to-gold-600 text-white"
        }`}
      >
        {isUser ? <User className="h-3.5 w-3.5" /> : <Bot className="h-3.5 w-3.5" />}
      </div>

      {/* Content */}
      <div className={`flex-1 max-w-[85%] ${isUser ? "flex flex-col items-end" : ""}`}>
        {isThinking ? (
          <ThinkingIndicator />
        ) : (
          <div
            className={`rounded-2xl px-4 py-3 ${
              isUser
                ? "bg-warm-100 text-text-primary"
                : "bg-surface-raised border border-border shadow-xs"
            }`}
          >
            <MarkdownContent content={message.content} />
            {isStreaming && <StreamingIndicator />}
          </div>
        )}

        {/* Actions */}
        {!isUser && !isStreaming && !isThinking && message.content && (
          <div className="flex items-center gap-1.5 mt-1.5 ml-1">
            <button
              onClick={handleCopy}
              className="p-1.5 rounded-lg text-text-tertiary hover:text-text-primary hover:bg-warm-100/60 transition-all"
              title="Copy"
            >
              {copied ? <Check className="h-3 w-3 text-success" /> : <Copy className="h-3 w-3" />}
            </button>

            {sources && sources.length > 0 && (
              <button
                onClick={() => setShowSources(!showSources)}
                className={`flex items-center gap-1.5 px-2 py-1 rounded-lg text-[11px] font-medium transition-all ${
                  showSources
                    ? "bg-accent-subtle text-gold-700"
                    : "text-text-tertiary hover:text-text-primary hover:bg-warm-100/60"
                }`}
              >
                <ScrollText className="h-3 w-3" />
                {sources.length} source{sources.length > 1 ? "s" : ""}
                <ChevronDown
                  className={`h-3 w-3 transition-transform duration-200 ${showSources ? "rotate-180" : ""}`}
                />
              </button>
            )}

            {!sources?.length && (
              <div className="flex items-center gap-1 text-[11px] text-text-tertiary">
                <Sparkles className="h-3 w-3 text-gold-500/50" />
                <span>Grounded</span>
              </div>
            )}
          </div>
        )}

        {/* Expandable sources */}
        {showSources && sources && sources.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="mt-2 space-y-1.5 overflow-hidden"
          >
            {sources.map((source, i) => (
              <div key={i} className="relative group">
                <button
                  onClick={() => openEvidence(source)}
                  className="w-full text-left card p-3 hover:shadow-sm transition-all group/card cursor-pointer"
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <BookOpen className="h-3 w-3 text-gold-500/50" />
                      <span className="text-[11px] font-medium text-gold-600">
                        {source.scripture || "Source"}
                      </span>
                      <span className="text-[10px] text-text-tertiary uppercase tracking-wider">
                        {source.level}
                      </span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="h-1 w-10 rounded-full bg-warm-100 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-gradient-to-r from-gold-500 to-gold-400"
                          style={{ width: `${source.score * 100}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-text-tertiary font-mono">
                        {(source.score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <p className="text-[11px] text-text-secondary line-clamp-2 leading-relaxed pr-6">
                    {source.text}
                  </p>
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    const { addBookmark, removeBookmark } = useBookmarkStore.getState();
                    const bookmarks = useBookmarkStore.getState().bookmarks;
                    const idx = bookmarks.findIndex(
                      (b) => b.text === source.text && b.scripture === source.scripture
                    );
                    if (idx >= 0) {
                      removeBookmark(idx);
                    } else {
                      addBookmark(source);
                    }
                  }}
                  className="absolute top-2.5 right-2.5 p-1 rounded-md transition-all opacity-0 group-hover:opacity-100"
                  title={useBookmarkStore.getState().isBookmarked(source) ? "Remove bookmark" : "Bookmark source"}
                >
                  {useBookmarkStore.getState().isBookmarked(source) ? (
                    <BookmarkCheck className="h-3 w-3 text-gold-500" />
                  ) : (
                    <Bookmark className="h-3 w-3 text-text-tertiary hover:text-text-primary" />
                  )}
                </button>
              </div>
            ))}
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
