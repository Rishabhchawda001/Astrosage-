"use client";

import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  MessageSquare,
  Trash2,
  PanelLeftClose,
  PanelLeft,
  Search,
} from "lucide-react";
import type { Conversation } from "@/types/api";

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
  conversations,
  currentId,
  onSelect,
  onNew,
  onDelete,
  isOpen,
  onToggle,
}: ConversationSidebarProps) {
  return (
    <AnimatePresence mode="wait">
      {isOpen ? (
        <motion.aside
          key="sidebar-open"
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: 300, opacity: 1 }}
          exit={{ width: 0, opacity: 0 }}
          transition={{ duration: 0.2, ease: "easeInOut" }}
          className="flex-shrink-0 border-r border-border bg-surface overflow-hidden"
        >
          <div className="w-[300px] h-full flex flex-col">
            {/* Header */}
            <div className="p-4 border-b border-border">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-sm font-semibold text-text-primary">Conversations</h2>
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
            </div>

            {/* Conversation list */}
            <div className="flex-1 overflow-y-auto p-2 space-y-1">
              {conversations.length === 0 ? (
                <div className="text-center py-8">
                  <MessageSquare className="h-8 w-8 mx-auto text-text-tertiary mb-2" />
                  <p className="text-xs text-text-tertiary">No conversations yet</p>
                </div>
              ) : (
                conversations.map((conv) => (
                  <div
                    key={conv.id}
                    className={`group flex items-center gap-3 px-3 py-2.5 rounded-xl cursor-pointer transition-all ${
                      conv.id === currentId
                        ? "bg-gold-500/10 border border-gold-500/20"
                        : "hover:bg-white/5 border border-transparent"
                    }`}
                    onClick={() => onSelect(conv.id)}
                  >
                    <MessageSquare className="h-4 w-4 flex-shrink-0 text-text-tertiary" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-text-primary truncate">
                        {conv.title || "New conversation"}
                      </p>
                      <p className="text-xs text-text-tertiary">
                        {conv.message_count} messages
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onDelete(conv.id);
                      }}
                      className="p-1.5 rounded-lg text-text-tertiary opacity-0 group-hover:opacity-100 hover:text-red-400 hover:bg-red-500/10 transition-all"
                      title="Delete conversation"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </motion.aside>
      ) : (
        <motion.button
          key="sidebar-closed"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onToggle}
          className="absolute left-4 top-20 z-20 p-2 rounded-lg glass text-text-tertiary hover:text-text-primary transition-all"
          title="Open sidebar"
        >
          <PanelLeft className="h-4 w-4" />
        </motion.button>
      )}
    </AnimatePresence>
  );
}
