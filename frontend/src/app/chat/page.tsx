"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Sparkles, BookOpen, MessageSquare, ArrowRight, Star } from "lucide-react";
import { Navigation } from "@/components/shared/Navigation";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ChatInput } from "@/components/chat/ChatInput";
import { ConversationSidebar } from "@/components/chat/ConversationSidebar";
import { EvidenceDrawer } from "@/components/shared/EvidenceDrawer";
import { StarField } from "@/components/landing/StarField";
import { useChatStore } from "@/lib/store";
import { chatStream, answer, conversations as convApi } from "@/lib/api";
import type { ChatMessage, EvidenceItem, Conversation } from "@/types/api";

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

  // Load conversations
  useEffect(() => {
    convApi.list().then(setConvList).catch(() => {});
  }, []);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isThinking]);

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
        } else {
          addMessage({
            role: "assistant",
            content: "I'm here to help explore Hindu scriptures. Please ask your question again, or try asking about a specific concept, entity, or scripture.",
          });
        }
      }
    );
    abortRef.current = abort;
  }, [messages, isStreaming, currentConversationId, addMessage, setStreaming, setConversationId, addConversation, setMessages]);

  const handleStop = useCallback(() => {
    abortRef.current?.();
    setStreaming(false);
    setIsThinking(false);
  }, [setStreaming]);

  return (
    <div className="relative h-screen flex flex-col">
      <StarField />
      <Navigation />

      <div className="flex flex-1 pt-16 overflow-hidden">
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

        {/* Main chat area */}
        <div className="flex-1 flex flex-col min-w-0 relative">
          {/* Chat header */}
          <div className="flex items-center justify-between px-6 py-3 border-b border-border bg-surface/50 backdrop-blur-sm">
            <div className="flex items-center gap-3">
              <BookOpen className="h-4 w-4 text-gold-400" />
              <span className="text-sm font-medium text-text-primary">
                {currentConversationId ? "Chat" : "New Chat"}
              </span>
              <span className="text-xs text-text-tertiary">·</span>
              <span className="text-xs text-text-tertiary flex items-center gap-1">
                <Sparkles className="h-3 w-3 text-gold-400/60" />
                Evidence-backed
              </span>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6">
            <div className="max-w-3xl mx-auto space-y-6">
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
          </div>

          {/* Input */}
          <ChatInput
            onSend={handleSend}
            onStop={handleStop}
            isStreaming={isStreaming}
          />
        </div>
      </div>

      <EvidenceDrawer />
    </div>
  );
}
