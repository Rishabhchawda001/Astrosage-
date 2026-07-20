// ── AstroSage Global State (Zustand) ──

import { create } from "zustand";
import type { Conversation, ChatMessage, EvidenceItem } from "@/types/api";

// ── Auth Store ──
interface AuthState {
  isAuthenticated: boolean;
  username: string | null;
  login: (username: string, token: string, refresh: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  isAuthenticated:
    typeof window !== "undefined" &&
    !!localStorage.getItem("astrosage_access_token"),
  username:
    typeof window !== "undefined"
      ? localStorage.getItem("astrosage_user")
      : null,
  login: (username, _token, _refresh) => {
    localStorage.setItem("astrosage_user", username);
    set({ isAuthenticated: true, username });
  },
  logout: () => {
    localStorage.removeItem("astrosage_access_token");
    localStorage.removeItem("astrosage_refresh_token");
    localStorage.removeItem("astrosage_user");
    set({ isAuthenticated: false, username: null });
  },
}));

// ── Chat Store ──
interface ChatState {
  messages: ChatMessage[];
  isStreaming: boolean;
  currentConversationId: string | null;
  conversations: Conversation[];
  pinnedConversations: string[]; // IDs of pinned conversations
  conversationSearch: string;
  addMessage: (msg: ChatMessage) => void;
  setMessages: (msgs: ChatMessage[]) => void;
  clearMessages: () => void;
  setStreaming: (v: boolean) => void;
  setConversationId: (id: string | null) => void;
  setConversations: (convs: Conversation[]) => void;
  addConversation: (conv: Conversation) => void;
  togglePinConversation: (id: string) => void;
  setConversationSearch: (q: string) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  messages: [],
  isStreaming: false,
  currentConversationId: null,
  conversations: [],
  pinnedConversations:
    typeof window !== "undefined"
      ? JSON.parse(localStorage.getItem("astrosage_pinned") || "[]")
      : [],
  conversationSearch: "",
  addMessage: (msg) =>
    set((s) => ({ messages: [...s.messages, msg] })),
  setMessages: (msgs) => set({ messages: msgs }),
  clearMessages: () => set({ messages: [] }),
  setStreaming: (v) => set({ isStreaming: v }),
  setConversationId: (id) => set({ currentConversationId: id }),
  setConversations: (convs) => set({ conversations: convs }),
  addConversation: (conv) =>
    set((s) => ({ conversations: [conv, ...s.conversations] })),
  togglePinConversation: (id) =>
    set((s) => {
      const pinned = s.pinnedConversations.includes(id)
        ? s.pinnedConversations.filter((p) => p !== id)
        : [id, ...s.pinnedConversations];
      localStorage.setItem("astrosage_pinned", JSON.stringify(pinned));
      return { pinnedConversations: pinned };
    }),
  setConversationSearch: (q) => set({ conversationSearch: q }),
}));

// ── Search Store ──
interface SearchState {
  query: string;
  results: EvidenceItem[];
  isSearching: boolean;
  setQuery: (q: string) => void;
  setResults: (r: EvidenceItem[]) => void;
  setSearching: (v: boolean) => void;
}

export const useSearchStore = create<SearchState>((set) => ({
  query: "",
  results: [],
  isSearching: false,
  setQuery: (q) => set({ query: q }),
  setResults: (r) => set({ results: r }),
  setSearching: (v) => set({ isSearching: v }),
}));

// ── UI Store ──
interface UIState {
  sidebarOpen: boolean;
  evidenceDrawerOpen: boolean;
  selectedEvidence: EvidenceItem | null;
  toggleSidebar: () => void;
  setSidebarOpen: (v: boolean) => void;
  openEvidence: (item: EvidenceItem) => void;
  closeEvidence: () => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  evidenceDrawerOpen: false,
  selectedEvidence: null,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebarOpen: (v) => set({ sidebarOpen: v }),
  openEvidence: (item) =>
    set({ evidenceDrawerOpen: true, selectedEvidence: item }),
  closeEvidence: () =>
    set({ evidenceDrawerOpen: false, selectedEvidence: null }),
}));


// ── Bookmarks Store ──
interface BookmarkState {
  bookmarks: EvidenceItem[];
  addBookmark: (item: EvidenceItem) => void;
  removeBookmark: (index: number) => void;
  isBookmarked: (item: EvidenceItem) => boolean;
}

export const useBookmarkStore = create<BookmarkState>((set, get) => ({
  bookmarks:
    typeof window !== "undefined"
      ? JSON.parse(localStorage.getItem("astrosage_bookmarks") || "[]")
      : [],
  addBookmark: (item) =>
    set((s) => {
      const exists = s.bookmarks.some(
        (b) => b.text === item.text && b.scripture === item.scripture
      );
      if (exists) return s;
      const bookmarks = [...s.bookmarks, item];
      localStorage.setItem("astrosage_bookmarks", JSON.stringify(bookmarks));
      return { bookmarks };
    }),
  removeBookmark: (index) =>
    set((s) => {
      const bookmarks = s.bookmarks.filter((_, i) => i !== index);
      localStorage.setItem("astrosage_bookmarks", JSON.stringify(bookmarks));
      return { bookmarks };
    }),
  isBookmarked: (item) =>
    get().bookmarks.some(
      (b) => b.text === item.text && b.scripture === item.scripture
    ),
}));
