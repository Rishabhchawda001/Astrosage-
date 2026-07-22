"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, BookOpen, MessageSquare, ArrowRight, Star, Search, Loader2, ScrollText, FileText, PanelLeft } from "lucide-react";
import { Navigation } from "@/components/shared/Navigation";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ChatInput } from "@/components/chat/ChatInput";
import { ConversationSidebar } from "@/components/chat/ConversationSidebar";
import { EvidenceDrawer } from "@/components/shared/EvidenceDrawer";
import { StarField } from "@/components/landing/StarField";
import { useChatStore } from "@/lib/store";
import { toast } from "sonner";
import { chatStream, answer, search as searchApi, conversations as convApi } from "@/lib/api";
import type { ChatMessage, EvidenceItem, Conversation, SearchResult as ApiSearchResult } from "@/types/api";

type ChatMode = "chat" | "search";

export default function ChatPage() {
  const {
    messages, isStreaming, currentConversationId,
    addMessage, setMessages, clearMessages,
    setStreaming, setConversationId, addConversation,
  } = useChatStore();

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [convList, setConvList] = useState<Conversation[]>([]);
  const [sources, setSources] = useState<Record<number, EvidenceItem[]>>({});
  const [isThinking, setIsThinking] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<() => void>(undefined);

  const [chatMode, setChatMode] = useState<ChatMode>("chat");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<ApiSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchTab, setSearchTab] = useState<"all" | "entities" | "verses">("all");
  const searchInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    convApi.list().then(setConvList).catch(() => {});
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      const textarea = document.querySelector('textarea[placeholder*="Ask about Hindu"]');
      if (textarea) (textarea as HTMLTextAreaElement).focus();
    }, 300);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  useEffect(() => {
    if (chatMode === "search") {
      setTimeout(() => searchInputRef.current?.focus(), 100);
    }
  }, [chatMode]);

  const handleSearch = useCallback(async (q: string) => {
    if (!q.trim()) return;
    setIsSearching(true);
    setSearchQuery(q);
    try {
      const res = await searchApi.query({ query: q.trim(), top_k: 20 });
      setSearchResults(res.results);
    } catch {
      toast.error("Search failed. Please try again.");
      setSearchResults([]);
    }
    setIsSearching(false);
  }, []);

  const handleSwitchMode = useCallback((mode: ChatMode) => {
    setChatMode(mode);
    setHasStarted(mode === "chat" ? messages.length > 0 : false);
  }, [messages.length]);

  const handleNewChat = useCallback(() => {
    clearMessages();
    setConversationId(null);
    setSources({});
    setHasStarted(false);
  }, [clearMessages, setConversationId]);

  const handleSelectConversation = useCallback(async (id: string) => {
    setConversationId(id);
    setHasStarted(true);
    try {
      const conv = await convApi.get(id);
      if (conv.messages) {
        setMessages(conv.messages.map((m) => ({
          role: m.role as "user" | "assistant" | "system",
          content: m.content,
        })));
      }
    } catch { /* ignore */ }
  }, [setConversationId, setMessages]);

  const handleDeleteConversation = useCallback(async (id: string) => {
    try {
      await convApi.delete(id);
      setConvList((prev) => prev.filter((c) => c.id !== id));
      if (currentConversationId === id) handleNewChat();
    } catch { /* ignore */ }
  }, [currentConversationId, handleNewChat]);

  const handleSend = useCallback(async (input: string) => {
    setHasStarted(true);
    const userMsg: ChatMessage = { role: "user", content: input };
    addMessage(userMsg);
    setStreaming(true);
    setIsThinking(true);

    await new Promise((r) => setTimeout(r, 400));
    setIsThinking(false);

    let answerResult: EvidenceItem[] = [];
    try {
      const answerResp = await answer.ask({ question: input, top_k: 5 });
      answerResult = answerResp.sources;
    } catch { /* fall back to LLM */ }

    let assistantContent = "";
    const assistantMsg: ChatMessage = { role: "assistant", content: "" };
    addMessage(assistantMsg);

    const stop = chatStream(
      {
        messages: [...messages, userMsg, { role: "system", content: "Answer using the provided evidence. Cite sources." }],
        stream: true,
      },
      (token) => {
        assistantContent += token;
        setMessages([
          ...useChatStore.getState().messages.slice(0, -1),
          { role: "assistant", content: assistantContent },
        ]);
      },
      () => {
        setStreaming(false);
        if (answerResult.length > 0) {
          const msgIdx = useChatStore.getState().messages.length - 1;
          setSources((prev) => ({ ...prev, [msgIdx]: answerResult }));
        }
      },
      (err) => {
        setStreaming(false);
        toast.error(err.message || "Failed to get response");
      }
    );

    abortRef.current = stop;
  }, [messages, addMessage, setStreaming, setMessages]);

  const handleStop = useCallback(() => {
    abortRef.current?.();
    setStreaming(false);
  }, [setStreaming]);

  const filteredSearchResults = useMemo(() => {
    if (searchTab === "all") return searchResults;
    if (searchTab === "entities") return searchResults.filter(r => r.level === "entity");
    return searchResults.filter(r => r.level === "verse");
  }, [searchResults, searchTab]);

  return (
    <div className="relative h-screen flex flex-col overflow-hidden">
      <StarField />
      <Navigation />

      <div className="relative z-10 flex flex-1 pt-16">
        {/* Sidebar */}
        <ConversationSidebar
          conversations={convList}
          currentId={currentConversationId}
          onSelect={handleSelectConversation}
          onNew={handleNewChat}
          onDelete={handleDeleteConversation}
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
        />

        {/* Main area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Mode switcher */}
          <div className="flex items-center gap-2 px-5 py-3 border-b border-border bg-surface/80 backdrop-blur-sm">
            <button
              onClick={() => handleSwitchMode("chat")}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all ${
                chatMode === "chat"
                  ? "bg-accent-subtle text-gold-700"
                  : "text-text-tertiary hover:text-text-primary hover:bg-warm-100/60"
              }`}
            >
              <MessageSquare className="h-3.5 w-3.5" />
              Chat
            </button>
            <button
              onClick={() => handleSwitchMode("search")}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all ${
                chatMode === "search"
                  ? "bg-accent-subtle text-gold-700"
                  : "text-text-tertiary hover:text-text-primary hover:bg-warm-100/60"
              }`}
            >
              <Search className="h-3.5 w-3.5" />
              Search
            </button>
          </div>

          {/* Content area */}
          <div className="flex-1 overflow-y-auto">
            {!hasStarted && chatMode === "chat" ? (
              /* Welcome state */
              <div className="flex flex-col items-center justify-center h-full px-6 text-center">
                <motion.div
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6, ease: "easeOut" }}
                >
                  <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-gold-500 to-gold-600 flex items-center justify-center mx-auto mb-5">
                    <Sparkles className="h-7 w-7 text-white" />
                  </div>
                  <h2 className="font-serif text-3xl font-bold text-text-primary mb-3 tracking-tight">
                    Ask AstroSage
                  </h2>
                  <p className="text-text-secondary text-base max-w-md mb-8 leading-relaxed">
                    Explore thousands of years of verified Hindu scripture.
                    Every answer is grounded in evidence.
                  </p>
                  <div className="flex flex-wrap justify-center gap-2 max-w-lg">
                    {[
                      "What is Dharma?",
                      "Tell me about the Bhagavad Gita",
                      "Who is Krishna?",
                      "What are the Vedas?",
                    ].map((q) => (
                      <button
                        key={q}
                        onClick={() => handleSend(q)}
                        className="px-4 py-2 rounded-xl bg-warm-50 border border-border text-sm text-text-secondary hover:text-text-primary hover:bg-warm-100 hover:border-border-strong transition-all"
                      >
                        {q}
                      </button>
                    ))}
                  </div>
                </motion.div>
              </div>
            ) : chatMode === "search" ? (
              /* Search mode */
              <div className="max-w-4xl mx-auto px-5 py-8">
                {/* Search input */}
                <div className="relative mb-6">
                  <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-text-tertiary" />
                  <input
                    ref={searchInputRef}
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleSearch(searchQuery)}
                    placeholder="Search entities, scriptures, concepts..."
                    className="w-full pl-12 pr-4 py-3.5 rounded-2xl glass text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-1 focus:ring-accent/30 transition-all"
                  />
                </div>

                {/* Tabs */}
                {searchResults.length > 0 && (
                  <div className="flex gap-1.5 mb-5">
                    {(["all", "entities", "verses"] as const).map((tab) => (
                      <button
                        key={tab}
                        onClick={() => setSearchTab(tab)}
                        className={`px-3 py-1.5 rounded-lg text-[13px] font-medium transition-all ${
                          searchTab === tab
                            ? "bg-accent-subtle text-gold-700 border border-gold-500/15"
                            : "text-text-tertiary hover:text-text-primary hover:bg-warm-100/60"
                        }`}
                      >
                        {tab === "all" ? "All" : tab.charAt(0).toUpperCase() + tab.slice(1)}
                        <span className="ml-1.5 text-xs opacity-60">
                          ({tab === "all" ? searchResults.length :
                            tab === "entities" ? searchResults.filter(r => r.level === "entity").length :
                            searchResults.filter(r => r.level === "verse").length})
                        </span>
                      </button>
                    ))}
                  </div>
                )}

                {/* Results */}
                {isSearching ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="h-6 w-6 animate-spin text-gold-500" />
                  </div>
                ) : filteredSearchResults.length > 0 ? (
                  <div className="space-y-3">
                    {filteredSearchResults.map((result, i) => (
                      <motion.div
                        key={result.chunk_id}
                        initial={{ opacity: 0, y: 8 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: i * 0.03, duration: 0.4, ease: "easeOut" }}
                        className="card p-5 hover:shadow-md transition-all group"
                      >
                        <div className="flex items-start gap-3">
                          <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-gradient-to-br from-gold-400/15 to-gold-500/15 flex items-center justify-center">
                            {result.level === "entity" ? (
                              <BookOpen className="h-4 w-4 text-gold-600" />
                            ) : result.level === "verse" ? (
                              <ScrollText className="h-4 w-4 text-gold-600" />
                            ) : (
                              <FileText className="h-4 w-4 text-gold-600" />
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-[11px] font-medium text-gold-600 uppercase tracking-wider">
                                {result.level}
                              </span>
                              {result.scripture_id && (
                                <>
                                  <span className="text-[11px] text-text-tertiary">·</span>
                                  <span className="text-[11px] text-text-tertiary">{result.scripture_id}</span>
                                </>
                              )}
                              <span className="ml-auto text-[11px] text-text-tertiary">
                                Score: {(result.score * 100).toFixed(0)}%
                              </span>
                            </div>
                            <p className="text-sm text-text-primary leading-relaxed line-clamp-3">
                              {result.text}
                            </p>
                            {result.entity_links && result.entity_links.length > 0 && (
                              <div className="flex flex-wrap gap-1.5 mt-2">
                                {result.entity_links.slice(0, 5).map((link, j) => (
                                  <span
                                    key={j}
                                    className="px-2 py-0.5 rounded-md bg-warm-100 text-[11px] text-text-secondary"
                                  >
                                    {link.name}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                ) : searchQuery && !isSearching ? (
                  <div className="text-center pt-12">
                    <Search className="h-12 w-12 mx-auto text-text-tertiary/20 mb-4" />
                    <p className="text-text-secondary">No results found for &ldquo;{searchQuery}&rdquo;</p>
                    <p className="text-text-tertiary text-sm mt-1">Try a different search term</p>
                  </div>
                ) : null}
              </div>
            ) : (
              /* Chat messages */
              <div className="max-w-3xl mx-auto px-5 py-6 space-y-5">
                {messages.map((msg, i) => (
                  <MessageBubble
                    key={i}
                    message={msg}
                    isStreaming={i === messages.length - 1 && isStreaming}
                    isThinking={i === messages.length - 1 && isThinking}
                    sources={sources[i]}
                  />
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input — only in chat mode */}
          {chatMode === "chat" && (
            <ChatInput
              onSend={handleSend}
              onStop={handleStop}
              isStreaming={isStreaming}
            />
          )}
        </div>
      </div>

      <EvidenceDrawer />
    </div>
  );
}
