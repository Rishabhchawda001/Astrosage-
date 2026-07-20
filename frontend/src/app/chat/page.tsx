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
import { chatStream, answer, search as searchApi, conversations as convApi } from "@/lib/api";
import type { ChatMessage, EvidenceItem, Conversation, SearchResult as ApiSearchResult } from "@/types/api";

type ChatMode = "chat" | "search";

export default function ChatPage() {
  const {
    messages, isStreaming, currentConversationId,
    conversations, addMessage, setMessages, clearMessages,
    setStreaming, setConversationId, setConversations, addConversation,
  } = useChatStore();

  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [convList, setConvList] = useState<Conversation[]>([]);
  const [sources, setSources] = useState<Record<number, EvidenceItem[]>>({});
  const [isThinking, setIsThinking] = useState(false);
  const [hasStarted, setHasStarted] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<() => void>(undefined);

  // Search mode state
  const [chatMode, setChatMode] = useState<ChatMode>("chat");
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<ApiSearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchTab, setSearchTab] = useState<"all" | "entities" | "verses">("all");
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Load conversations
  useEffect(() => {
    convApi.list().then(setConvList).catch(() => {});
  }, []);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

  // Focus search input when switching to search mode
  useEffect(() => {
    if (chatMode === "search") {
      setTimeout(() => searchInputRef.current?.focus(), 100);
    }
  }, [chatMode]);

  // Handle search
  const handleSearch = useCallback(async (q: string) => {
    if (!q.trim()) return;
    setIsSearching(true);
    setSearchQuery(q);
    try {
      const res = await searchApi.query({ query: q.trim(), top_k: 20 });
      setSearchResults(res.results);
    } catch {
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

    // Brief thinking pause for UX
    await new Promise((r) => setTimeout(r, 400));
    setIsThinking(false);

    // Get answer from knowledge base
    let answerResult: EvidenceItem[] = [];
    try {
      const answerResp = await answer.ask({ question: input, top_k: 5 });
      answerResult = answerResp.sources;
    } catch { /* fall back to LLM */ }

    // Create conversation if needed
    let convId = currentConversationId;
    if (!convId) {
      try {
        const conv = await convApi.create();
        convId = conv.id;
        // Auto-title with first user message
        if (conv.title === "New conversation") {
          convApi.updateTitle(convId, input.slice(0, 60)).catch(() => {});
        }
        setConversationId(convId);
        addConversation(conv);
        setConvList((prev) => [conv, ...prev]);
        await convApi.addMessage(convId, "user", input);
      } catch { /* continue without persistence */ }
    } else {
      try { await convApi.addMessage(convId, "user", input); } catch { /* ignore */ }
    }

    // Stream the response
    let assistantContent = "";
    const msgIndex = messages.length + 1;
    const abort = chatStream(
      { messages: [...messages, userMsg], stream: true },
      (token) => {
        assistantContent += token;
        const prev = useChatStore.getState().messages;
        const last = prev[prev.length - 1];
        if (last?.role === "assistant") {
          setMessages([...prev.slice(0, -1), { ...last, content: assistantContent }]);
        } else {
          addMessage({ role: "assistant", content: assistantContent });
        }
      },
      () => {
        setStreaming(false);
        if (answerResult.length > 0) {
          setSources((prev) => ({ ...prev, [msgIndex]: answerResult }));
        }
        if (convId) {
          convApi.addMessage(convId, "assistant", assistantContent).catch(() => {});
        }
      },
      () => {
        setStreaming(false);
        if (answerResult.length > 0) {
          const fallbackText = `Based on my knowledge of Hindu scriptures, here's what I found:\n\n${
            answerResult.slice(0, 3).map((s, i) =>
              `**Source ${i + 1}** (${s.scripture || "Scripture"}, relevance: ${(s.score * 100).toFixed(0)}%):\n${s.text}`
            ).join("\n\n")
          }`;
          addMessage({ role: "assistant", content: fallbackText });
          setSources((prev) => ({ ...prev, [msgIndex]: answerResult }));
        }
        if (convId) {
          convApi.addMessage(convId, "assistant", assistantContent || "I encountered an error processing your request.").catch(() => {});
        }
      }
    );
    abortRef.current = abort;
  }, [messages, addMessage, setStreaming, currentConversationId, setConversationId, addConversation, setConvList]);

  const handleStop = useCallback(() => {
    if (abortRef.current) {
      abortRef.current();
      abortRef.current = undefined;
    }
    setStreaming(false);
    setIsThinking(false);
  }, [setStreaming]);

  const filteredResults = useMemo(() => {
    if (searchTab === "all") return searchResults;
    if (searchTab === "entities") return searchResults.filter(r => r.level === "entity");
    if (searchTab === "verses") return searchResults.filter(r => r.level === "verse");
    return searchResults;
  }, [searchResults, searchTab]);

  return (
    <div className="relative min-h-screen">
      <StarField />
      <Navigation />

      <div className="relative z-10 pt-16 flex h-[calc(100vh-4rem)]">
        {/* Sidebar */}
        <ConversationSidebar
          conversations={convList}
          currentId={currentConversationId}
          onSelect={handleSelectConversation}
          onNew={handleNewChat}
          onDelete={handleDeleteConversation}
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(v => !v)}
        />

        {/* Main chat area */}
        <div className="flex-1 flex flex-col min-w-0 relative">
          {/* Chat header */}
          <div className="flex items-center justify-between px-6 py-3 border-b border-border bg-surface/60 backdrop-blur-sm">
            <div className="flex items-center gap-3">
              {/* Mode toggle */}
              <div className="flex items-center gap-1.5 bg-surface-elevated rounded-xl p-0.5 border border-border/50">
                <button
                  onClick={() => handleSwitchMode("chat")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    chatMode === "chat"
                      ? "bg-gold-500/15 text-gold-400 shadow-sm"
                      : "text-text-tertiary hover:text-text-primary"
                  }`}
                >
                  <MessageSquare className="h-3.5 w-3.5" />
                  Chat
                </button>
                <button
                  onClick={() => handleSwitchMode("search")}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    chatMode === "search"
                      ? "bg-gold-500/15 text-gold-400 shadow-sm"
                      : "text-text-tertiary hover:text-text-primary"
                  }`}
                >
                  <Search className="h-3.5 w-3.5" />
                  Knowledge Search
                </button>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {chatMode === "chat" && (
                <span className="text-xs text-text-tertiary flex items-center gap-1">
                  <Sparkles className="h-3 w-3 text-gold-400/60" />
                  Evidence-backed
                </span>
              )}
              <button
                onClick={() => setSidebarOpen(v => !v)}
                className="p-1.5 rounded-lg text-text-tertiary hover:text-text-primary hover:bg-white/5 transition-all lg:hidden"
                title="Toggle sidebar"
              >
                <PanelLeft className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Content area — switches between chat and search */}
          <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6">
            <div className="max-w-3xl mx-auto">
              {chatMode === "chat" ? (
                /* ── CHAT MODE ── */
                <div className="space-y-6">
                  <AnimatePresence mode="popLayout">
                    {messages.map((msg, i) => (
                      <MessageBubble
                        key={`msg-${i}`}
                        message={msg}
                        isStreaming={isStreaming && i === messages.length - 1 && msg.role === "assistant" && !isThinking}
                        isThinking={isThinking && i === messages.length - 1 && msg.role === "user"}
                        sources={sources[i + 1]}
                      />
                    ))}
                  </AnimatePresence>

                  {/* Thinking indicator shown between user msg and response */}
                  {isThinking && (
                    <MessageBubble
                      message={{ role: "assistant" as const, content: "" }}
                      isThinking={true}
                    />
                  )}

                  {/* Empty state */}
                  {!hasStarted && (
                    <motion.div
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex flex-col items-center justify-center min-h-[60vh] text-center"
                    >
                      <motion.div
                        initial={{ scale: 0.9 }}
                        animate={{ scale: 1 }}
                        transition={{ duration: 0.5 }}
                        className="w-20 h-20 rounded-3xl bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center mb-8 shadow-2xl shadow-gold-500/20"
                      >
                        <Star className="h-10 w-10 text-surface" />
                      </motion.div>

                      <h2 className="font-serif text-3xl sm:text-4xl font-bold text-text-primary mb-4">
                        Ask <span className="gradient-gold">Anything</span>
                      </h2>
                      <p className="text-text-secondary text-base max-w-md mb-10 leading-relaxed">
                        Explore Hindu scriptures with evidence-backed answers.
                        Every response is grounded in canonical sources you can verify.
                      </p>

                      {/* Suggested questions */}
                      <div className="grid sm:grid-cols-2 gap-2.5 w-full max-w-lg">
                        {[
                          { q: "Who is Vishnu?", icon: "🕉" },
                          { q: "What is Dharma?", icon: "☸" },
                          { q: "Explain the concept of Karma", icon: "🔄" },
                          { q: "What does the Bhagavad Gita say about duty?", icon: "📜" },
                        ].map((item) => (
                          <button
                            key={item.q}
                            onClick={() => handleSend(item.q)}
                            disabled={isStreaming}
                            className="group flex items-center gap-3 glass rounded-xl px-4 py-3.5 text-left text-sm text-text-secondary hover:text-text-primary hover:bg-white/[0.04] transition-all disabled:opacity-50 border border-transparent hover:border-gold-500/10"
                          >
                            <span className="text-base">{item.icon}</span>
                            <span className="flex-1">{item.q}</span>
                            <ArrowRight className="h-3.5 w-3.5 text-text-tertiary opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-200" />
                          </button>
                        ))}
                      </div>
                    </motion.div>
                  )}

                  <div ref={messagesEndRef} />
                </div>
              ) : (
                /* ── SEARCH MODE ── */
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex flex-col min-h-[60vh]"
                >
                  {/* Search bar */}
                  <div className="relative mb-8">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-text-tertiary" />
                    <input
                      ref={searchInputRef}
                      type="text"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleSearch(searchQuery)}
                      placeholder="Search scriptures, entities, concepts..."
                      className="w-full pl-12 pr-4 py-4 rounded-2xl glass text-text-primary placeholder-text-tertiary text-lg focus:outline-none focus:ring-1 focus:ring-gold-500/30 transition-all"
                    />
                    <button
                      onClick={() => handleSearch(searchQuery)}
                      disabled={!searchQuery.trim() || isSearching}
                      className="absolute right-3 top-1/2 -translate-y-1/2 px-5 py-2 rounded-xl bg-gold-500 text-surface text-sm font-semibold hover:bg-gold-400 transition-all disabled:opacity-30"
                    >
                      {isSearching ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        "Search"
                      )}
                    </button>
                  </div>

                  {/* Search empty state */}
                  {searchResults.length === 0 && !isSearching && !searchQuery && (
                    <div className="flex flex-col items-center justify-center flex-1 text-center">
                      <motion.div
                        initial={{ scale: 0.9 }}
                        animate={{ scale: 1 }}
                        transition={{ duration: 0.5 }}
                        className="w-20 h-20 rounded-3xl bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center mb-8 shadow-2xl shadow-gold-500/20"
                      >
                        <Search className="h-10 w-10 text-surface" />
                      </motion.div>

                      <h2 className="font-serif text-3xl sm:text-4xl font-bold text-text-primary mb-4">
                        Knowledge <span className="gradient-gold">Search</span>
                      </h2>
                      <p className="text-text-secondary text-base max-w-md mb-10 leading-relaxed">
                        Search across 120K+ scripture chunks, 391 entities, and 54 scriptures.
                        Find evidence-backed knowledge instantly.
                      </p>

                      {/* Suggested search queries */}
                      <div className="grid sm:grid-cols-2 gap-2.5 w-full max-w-lg">
                        {[
                          { q: "Vishnu avataras", icon: "🕉" },
                          { q: "Bhagavad Gita verses on karma", icon: "📜" },
                          { q: "Rama and Sita", icon: "🏹" },
                          { q: "Pandavas Mahabharata", icon: "⚔️" },
                        ].map((item) => (
                          <button
                            key={item.q}
                            onClick={() => handleSearch(item.q)}
                            disabled={isSearching}
                            className="group flex items-center gap-3 glass rounded-xl px-4 py-3.5 text-left text-sm text-text-secondary hover:text-text-primary hover:bg-white/[0.04] transition-all disabled:opacity-50 border border-transparent hover:border-gold-500/10"
                          >
                            <span className="text-base">{item.icon}</span>
                            <span className="flex-1">{item.q}</span>
                            <ArrowRight className="h-3.5 w-3.5 text-text-tertiary opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-200" />
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Search results */}
                  {searchResults.length > 0 && (
                    <>
                      {/* Tabs */}
                      <div className="flex gap-2 mb-6">
                        {(["all", "entities", "verses"] as const).map((tab) => (
                          <button
                            key={tab}
                            onClick={() => setSearchTab(tab)}
                            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                              searchTab === tab
                                ? "bg-gold-500/10 text-gold-400 border border-gold-500/20"
                                : "text-text-tertiary hover:text-text-primary hover:bg-white/5"
                            }`}
                          >
                            {tab === "all" ? "All Results" : tab.charAt(0).toUpperCase() + tab.slice(1)}
                            <span className="ml-1.5 text-xs opacity-60">
                              ({tab === "all" ? searchResults.length :
                                tab === "entities" ? searchResults.filter(r => r.level === "entity").length :
                                searchResults.filter(r => r.level === "verse").length})
                            </span>
                          </button>
                        ))}
                      </div>

                      {/* Results */}
                      <div className="space-y-4">
                        {filteredResults.map((result, i) => (
                          <motion.div
                            key={result.chunk_id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.03 }}
                            className="glass rounded-2xl p-5 hover:bg-white/[0.04] transition-all group"
                          >
                            <div className="flex items-start gap-3">
                              <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-gradient-to-br from-gold-400/20 to-gold-600/20 flex items-center justify-center">
                                {result.level === "entity" ? (
                                  <BookOpen className="h-5 w-5 text-gold-400" />
                                ) : result.level === "verse" ? (
                                  <ScrollText className="h-5 w-5 text-gold-400" />
                                ) : (
                                  <FileText className="h-5 w-5 text-gold-400" />
                                )}
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="text-xs font-medium text-gold-400 uppercase tracking-wider">
                                    {result.level}
                                  </span>
                                  {result.scripture_id && (
                                    <>
                                      <span className="text-xs text-text-tertiary">·</span>
                                      <span className="text-xs text-text-tertiary">{result.scripture_id}</span>
                                    </>
                                  )}
                                  <span className="ml-auto text-xs text-text-tertiary">
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
                                        className="px-2 py-0.5 rounded-md bg-white/5 text-xs text-text-secondary"
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

                        {filteredResults.length === 0 && (
                          <div className="text-center py-12">
                            <p className="text-text-tertiary">No results in this category</p>
                          </div>
                        )}
                      </div>
                    </>
                  )}

                  {searchQuery && !isSearching && searchResults.length === 0 && (
                    <div className="text-center pt-12">
                      <Search className="h-12 w-12 mx-auto text-text-tertiary mb-4" />
                      <p className="text-text-secondary">No results found for &ldquo;{searchQuery}&rdquo;</p>
                      <p className="text-text-tertiary text-sm mt-1">Try a different search term</p>
                    </div>
                  )}
                </motion.div>
              )}
            </div>
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
