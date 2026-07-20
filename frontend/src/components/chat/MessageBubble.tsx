"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  User, Bot, ChevronDown, ExternalLink, Copy, Check,
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
                <div className="text-xs text-text-tertiary px-3 py-1.5 border-b border-border bg-white/[0.02] rounded-t-xl">
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
      className="inline-flex items-center gap-1.5 ml-1"
    >
      <motion.span
        animate={{ opacity: [0.2, 1, 0.2] }}
        transition={{ duration: 1.2, repeat: Infinity, delay: 0 }}
        className="w-2 h-2 rounded-full bg-gradient-to-br from-gold-400 to-gold-600"
      />
      <motion.span
        animate={{ opacity: [0.2, 1, 0.2] }}
        transition={{ duration: 1.2, repeat: Infinity, delay: 0.2 }}
        className="w-2 h-2 rounded-full bg-gradient-to-br from-gold-400 to-gold-600"
      />
      <motion.span
        animate={{ opacity: [0.2, 1, 0.2] }}
        transition={{ duration: 1.2, repeat: Infinity, delay: 0.4 }}
        className="w-2 h-2 rounded-full bg-gradient-to-br from-gold-400 to-gold-600"
      />
    </motion.span>
  );
}

function ThinkingIndicator() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-3 px-4 py-3 rounded-xl glass max-w-fit"
    >
      <div className="flex items-center gap-1">
        <motion.div
          animate={{ scale: [1, 1.3, 1] }}
          transition={{ duration: 1, repeat: Infinity, delay: 0 }}
          className="w-1.5 h-1.5 rounded-full bg-gold-400/60"
        />
        <motion.div
          animate={{ scale: [1, 1.3, 1] }}
          transition={{ duration: 1, repeat: Infinity, delay: 0.15 }}
          className="w-1.5 h-1.5 rounded-full bg-gold-400/60"
        />
        <motion.div
          animate={{ scale: [1, 1.3, 1] }}
          transition={{ duration: 1, repeat: Infinity, delay: 0.3 }}
          className="w-1.5 h-1.5 rounded-full bg-gold-400/60"
        />
      </div>
      <span className="text-xs text-text-secondary font-medium">
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
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={`flex gap-4 ${isUser ? "flex-row-reverse" : ""}`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ring-2 ring-white/5 ${
          isUser
            ? "bg-gold-500/15 text-gold-400 ring-gold-500/10"
            : "bg-gradient-to-br from-gold-400 to-gold-600 text-surface ring-gold-500/20"
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      {/* Content */}
      <div className={`flex-1 max-w-[85%] ${isUser ? "flex flex-col items-end" : ""}`}>
        {isThinking ? (
          <ThinkingIndicator />
        ) : (
          <>
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
                <div className="relative">
                  <MarkdownContent content={message.content} />
                  {isStreaming && (
                    <motion.div
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="inline-block"
                    >
                      <StreamingIndicator />
                    </motion.div>
                  )}
                </div>
              )}
            </div>

            {/* Actions bar */}
            <div className={`flex items-center gap-1 mt-1.5 ${isUser ? "justify-end" : ""}`}>
              <button
                onClick={handleCopy}
                className="p-1.5 rounded-lg text-text-tertiary hover:text-text-primary hover:bg-white/5 transition-all"
                title="Copy message"
              >
                {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
              </button>

              {sources && sources.length > 0 && !isStreaming && (
                <button
                  onClick={() => setShowSources(!showSources)}
                  className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium transition-all ${
                    showSources
                      ? "bg-gold-500/15 text-gold-400"
                      : "text-text-tertiary hover:text-text-primary hover:bg-white/5"
                  }`}
                >
                  <ScrollText className="h-3 w-3" />
                  {sources.length} source{sources.length > 1 ? "s" : ""}
                  <ChevronDown
                    className={`h-3 w-3 transition-transform duration-200 ${
                      showSources ? "rotate-180" : ""
                    }`}
                  />
                </button>
              )}

              {!isUser && !isStreaming && !sources?.length && (
                <div className="flex items-center gap-1 text-xs text-text-tertiary">
                  <Sparkles className="h-3 w-3 text-gold-400/60" />
                  <span>Grounded</span>
                </div>
              )}
            </div>

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
                  <div className="relative group">
                    <button
                      onClick={() => openEvidence(source)}
                      className="w-full text-left glass rounded-xl p-3 hover:bg-white/[0.04] transition-all group/card border border-transparent hover:border-gold-500/10"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                          <BookOpen className="h-3 w-3 text-gold-400/60" />
                          <span className="text-xs font-medium text-gold-400">
                            {source.scripture || "Source"}
                          </span>
                          <span className="text-[10px] text-text-tertiary uppercase tracking-wider">
                            {source.level}
                          </span>
                        </div>
                        <div className="flex items-center gap-1.5">
                          <div className="h-1.5 w-12 rounded-full bg-white/5 overflow-hidden">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-gold-400 to-gold-600"
                              style={{ width: `${source.score * 100}%` }}
                            />
                          </div>
                          <span className="text-[10px] text-text-tertiary font-mono">
                            {(source.score * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>
                      <p className="text-xs text-text-secondary line-clamp-2 leading-relaxed pr-6">
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
                      className="absolute top-3 right-3 p-1.5 rounded-lg transition-all opacity-0 group-hover:opacity-100
                        {useBookmarkStore.getState().isBookmarked(source)
                          ? 'text-gold-400 hover:bg-gold-500/10 bg-gold-500/10'
                          : 'text-text-tertiary hover:text-text-primary hover:bg-white/5'}"
                      title={useBookmarkStore.getState().isBookmarked(source) ? "Remove bookmark" : "Bookmark source"}
                    >
                      {useBookmarkStore.getState().isBookmarked(source)
                        ? <BookmarkCheck className="h-3 w-3" />
                        : <Bookmark className="h-3 w-3" />}
                    </button>
                  </div>
                ))}
              </motion.div>
            )}
          </>
        )}
      </div>
    </motion.div>
  );
}
