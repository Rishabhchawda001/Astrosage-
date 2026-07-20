"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import { Sparkles, BookOpen } from "lucide-react";
import { Navigation } from "@/components/shared/Navigation";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ChatInput } from "@/components/chat/ChatInput";
import { ConversationSidebar } from "@/components/chat/ConversationSidebar";
import { EvidenceDrawer } from "@/components/shared/EvidenceDrawer";
import { StarField } from "@/components/landing/StarField";
import { useChatStore, useAuthStore } from "@/lib/store";
import { chatStream, answer, conversations as convApi, search } from "@/lib/api";
import type { ChatMessage, EvidenceItem, Conversation } from "@/types/api";

export default function ChatPage() {
  const {
    messages, isStreaming, currentConversationId,
    conversations, addMessage, setMessages, clearMessages,
    setStreaming, setConversationId, setConversations, addConversation,
  } = useChatStore();

  const { isAuthenticated } = useAuthStore();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [convList, setConvList] = useState<Conversation[]>([]);
  const [sources, setSources] = useState<Record<number, EvidenceItem[]>>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<() => void>(undefined);

  // Load conversations
  useEffect(() => {
    if (isAuthenticated) {
      convApi.list().then(setConvList).catch(() => {});
    }
  }, [isAuthenticated]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleNewChat = useCallback(() => {
    clearMessages();
    setConversationId(null);
    setSources({});
  }, [clearMessages, setConversationId]);

  const handleSelectConversation = useCallback(async (id: string) => {
    setConversationId(id);
    try {
      const conv = await convApi.get(id);
      if (conv.messages) {
        setMessages(conv.messages.map((m) => ({
          role: m.role as "user" | "assistant" | "system",
          content: m.content,
        })));
      }
    } catch {
      // Handle error silently
    }
  }, [setConversationId, setMessages]);

  const handleDeleteConversation = useCallback(async (id: string) => {
    try {
      await convApi.delete(id);
      setConvList((prev) => prev.filter((c) => c.id !== id));
      if (currentConversationId === id) {
        handleNewChat();
      }
    } catch {
      // Handle error silently
    }
  }, [currentConversationId, handleNewChat]);

  const handleSend = useCallback(async (input: string) => {
    const userMsg: ChatMessage = { role: "user", content: input };
    addMessage(userMsg);
    setStreaming(true);

    // Get answer from knowledge base
    let answerResult: EvidenceItem[] = [];
    try {
      const answerResp = await answer.ask({ question: input, top_k: 5 });
      answerResult = answerResp.sources;
    } catch {
      // Fall back to LLM-only
    }

    // Create or get conversation
    let convId = currentConversationId;
    if (isAuthenticated && !convId) {
      try {
        const conv = await convApi.create();
        convId = conv.id;
        setConversationId(convId);
        addConversation(conv);
        setConvList((prev) => [conv, ...prev]);
        await convApi.addMessage(convId, "user", input);
      } catch {
        // Continue without persistence
      }
    } else if (isAuthenticated && convId) {
      try {
        await convApi.addMessage(convId, "user", input);
      } catch {
        // Continue without persistence
      }
    }

    // Stream the response
    let assistantContent = "";
    const msgIndex = messages.length + 1;
    const abort = chatStream(
      { messages: [...messages, userMsg], stream: true },
      (token) => {
        assistantContent += token;
        // Update the last assistant message in real-time

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
        // Save assistant message to conversation
        if (isAuthenticated && convId) {
          convApi.addMessage(convId, "assistant", assistantContent).catch(() => {});
        }
      },
      () => {
        setStreaming(false);
        // Fallback: if streaming fails, use knowledge base answer
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
            content: "I apologize, but I'm having trouble retrieving an answer right now. Please try asking your question again.",
          });
        }
      }
    );
    abortRef.current = abort;
  }, [messages, isStreaming, currentConversationId, isAuthenticated, addMessage, setStreaming, setConversationId, addConversation, setMessages]);

  const handleStop = useCallback(() => {
    abortRef.current?.();
    setStreaming(false);
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
              <span className="text-xs text-text-tertiary">Evidence-backed answers</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5 text-xs text-gold-400">
                <Sparkles className="h-3 w-3" />
                <span>Grounded</span>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-6">
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full min-h-[60vh] text-center">
                  <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="max-w-md"
                  >
                    <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center mx-auto mb-6">
                      <BookOpen className="h-8 w-8 text-surface" />
                    </div>
                    <h2 className="font-serif text-2xl font-bold text-text-primary mb-3">
                      Ask Anything
                    </h2>
                    <p className="text-text-secondary leading-relaxed mb-8">
                      Explore Hindu scriptures with evidence-backed answers.
                      Every response is grounded in canonical sources.
                    </p>

                    {/* Example questions */}
                    <div className="space-y-2">
                      {[
                        "Who is Vishnu?",
                        "What is Dharma?",
                        "Explain the concept of Karma",
                        "What does the Bhagavad Gita say about duty?",
                      ].map((q) => (
                        <button
                          key={q}
                          onClick={() => handleSend(q)}
                          disabled={isStreaming}
                          className="w-full text-left glass rounded-xl px-4 py-3 text-sm text-text-secondary hover:text-text-primary hover:bg-white/[0.04] transition-all disabled:opacity-50"
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </motion.div>
                </div>
              ) : (
                messages.map((msg, i) => (
                  <MessageBubble
                    key={i}
                    message={msg}
                    isStreaming={isStreaming && i === messages.length - 1 && msg.role === "assistant"}
                    sources={sources[i + 1]}
                  />
                ))
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

      {/* Evidence drawer */}
      <EvidenceDrawer />
    </div>
  );
}
