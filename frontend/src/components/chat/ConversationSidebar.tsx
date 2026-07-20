"use client";

import { useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus, MessageSquare, Trash2, PanelLeftClose, PanelLeft,
  Search, Pin, PinOff, Clock, Star
} from "lucide-react";
import type { Conversation } from "@/types/api";
import { useChatStore } from "@/lib/store";

interface ConversationSidebarProps {
  conversations: Conversation[];
  currentId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  isOpen: boolean;
  onToggle: () => void;
}

export function ConversationSidebar({
  conversations, currentId, onSelect,
  onNew, onDelete, isOpen, onToggle,
}: ConversationSidebarProps) {
  const { pinnedConversations, togglePinConversation, conversationSearch, setConversationSearch } = useChatStore();

  // Filter and sort conversations
  const { pinned, recent } = useMemo(() => {
    const search = conversationSearch.toLowerCase();
    const filtered = search
      ? conversations.filter((c) =>
          (c.title || "").toLowerCase().includes(search)
        )
      : conversations;

    return {
      pinned: filtered.filter((c) => pinnedConversations.includes(c.id)),
      recent: filtered.filter((c) => !pinnedConversations.includes(c.id)),
    };
  }, [conversations, pinnedConversations, conversationSearch]);

  const hasPinned = pinned.length > 0;

  return (
    <AnimatePresence mode="wait">
      {isOpen ? (
        <motion.aside
          key="open"
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: 300, opacity: 1 }}
          exit={{ width: 0, opacity: 0 }}
          transition={{ duration: 0.2, ease: "easeInOut" }}
          className="flex-shrink-0 border-r border-border bg-surface overflow-hidden"
        >
          <div className="w-[300px] h-full flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-border space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-text-primary tracking-wide">
                  Conversations
                </h2>
                <button
                  onClick={onToggle}
                  className="p-1.5 rounded-lg text-text-tertiary hover:text-text-primary hover:bg-white/5 transition-all"
                  title="Close sidebar"
                >
                  <PanelLeftClose className="h-4 w-4" />
                </button>
              </div>

              <button
                onClick={onNew}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-gold-500 text-surface text-sm font-semibold hover:bg-gold-400 transition-all"
              >
                <Plus className="h-4 w-4" />
                New Chat
              </button>

              {/* Search */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-tertiary" />
                <input
                  type="text"
                  value={conversationSearch}
                  onChange={(e) => setConversationSearch(e.target.value)}
                  placeholder="Search conversations..."
                  className="w-full bg-surface-elevated rounded-lg pl-9 pr-3 py-2 text-xs text-text-primary placeholder-text-tertiary border border-border focus:outline-none focus:ring-1 focus:ring-gold-500/20"
                />
              </div>
            </div>

            {/* Conversation list */}
            <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
              {conversations.length === 0 && !conversationSearch ? (
                <div className="text-center py-12">
                  <MessageSquare className="h-8 w-8 mx-auto text-text-tertiary mb-3" />
                  <p className="text-xs text-text-tertiary">No conversations yet</p>
                  <p className="text-[10px] text-text-tertiary mt-1">
                    Start a new chat to begin
                  </p>
                </div>
              ) : (
                <>
                  {/* Pinned section */}
                  {hasPinned && (
                    <>
                      <div className="flex items-center gap-1.5 px-3 py-2">
                        <Star className="h-3 w-3 text-gold-400/60" />
                        <span className="text-[10px] text-text-tertiary uppercase tracking-wider font-medium">
                          Pinned
                        </span>
                      </div>
                      {pinned.map((conv) => (
                        <ConvItem
                          key={conv.id}
                          conv={conv}
                          isActive={conv.id === currentId}
                          isPinned={true}
                          onSelect={onSelect}
                          onDelete={onDelete}
                          onTogglePin={togglePinConversation}
                        />
                      ))}
                      <div className="h-px bg-border/50 mx-3 my-2" />
                    </>
                  )}

                  {/* Recent section */}
                  {recent.length > 0 && (
                    <div className="flex items-center gap-1.5 px-3 py-2">
                      <Clock className="h-3 w-3 text-text-tertiary/60" />
                      <span className="text-[10px] text-text-tertiary uppercase tracking-wider font-medium">
                        {hasPinned ? "Recent" : "All Conversations"}
                      </span>
                    </div>
                  )}

                  {recent.slice(0, 50).map((conv) => (
                    <ConvItem
                      key={conv.id}
                      conv={conv}
                      isActive={conv.id === currentId}
                      isPinned={false}
                      onSelect={onSelect}
                      onDelete={onDelete}
                      onTogglePin={togglePinConversation}
                    />
                  ))}

                  {conversationSearch && pinned.length === 0 && recent.length === 0 && (
                    <div className="text-center py-8">
                      <Search className="h-6 w-6 mx-auto text-text-tertiary mb-2" />
                      <p className="text-xs text-text-tertiary">No matching conversations</p>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </motion.aside>
      ) : (
        <motion.button
          key="closed"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onToggle}
          className="absolute left-4 top-20 z-20 p-2.5 rounded-xl glass text-text-tertiary hover:text-text-primary transition-all border border-border hover:border-gold-500/20"
          title="Open sidebar"
        >
          <PanelLeft className="h-4 w-4" />
        </motion.button>
      )}
    </AnimatePresence>
  );
}

function ConvItem({
  conv, isActive, isPinned, onSelect, onDelete, onTogglePin,
}: {
  conv: Conversation;
  isActive: boolean;
  isPinned: boolean;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onTogglePin: (id: string) => void;
}) {
  return (
    <div
      className={`group flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer transition-all ${
        isActive
          ? "bg-gold-500/10 border border-gold-500/20"
          : "hover:bg-white/[0.03] border border-transparent"
      }`}
      onClick={() => onSelect(conv.id)}
    >
      <MessageSquare className="h-3.5 w-3.5 flex-shrink-0 text-text-tertiary" />
      <div className="flex-1 min-w-0">
        <p className="text-xs text-text-primary truncate leading-5 font-medium">
          {conv.title || "New conversation"}
        </p>
        <p className="text-[10px] text-text-tertiary">
          {conv.message_count} message{conv.message_count !== 1 ? "s" : ""}
        </p>
      </div>
      <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={(e) => { e.stopPropagation(); onTogglePin(conv.id); }}
          className={`p-1 rounded-md transition-all ${
            isPinned
              ? "text-gold-400 hover:bg-gold-500/10"
              : "text-text-tertiary hover:text-text-primary hover:bg-white/5"
          }`}
          title={isPinned ? "Unpin" : "Pin"}
        >
          {isPinned ? <PinOff className="h-3 w-3" /> : <Pin className="h-3 w-3" />}
        </button>
        <button
          onClick={(e) => { e.stopPropagation(); onDelete(conv.id); }}
          className="p-1 rounded-md text-text-tertiary hover:text-red-400 hover:bg-red-500/10 transition-all"
          title="Delete"
        >
          <Trash2 className="h-3 w-3" />
        </button>
      </div>
    </div>
  );
}
