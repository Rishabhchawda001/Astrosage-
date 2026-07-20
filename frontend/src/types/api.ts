// ── AstroSage API TypeScript Types ──

// Search
export interface SearchRequest {
  query: string;
  top_k?: number;
  level?: string;
  scripture?: string;
}

export interface SearchResult {
  chunk_id: string;
  level: string;
  scripture_id: string;
  text: string;
  score: number;
  entity_links: { name: string; guid?: string }[];
  provenance: Record<string, unknown>;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total_results: number;
  latency_ms: number;
}

// Answer
export interface AnswerRequest {
  question: string;
  top_k?: number;
}

export interface EvidenceItem {
  text: string;
  scripture: string;
  level: string;
  score: number;
}

export interface AnswerBody {
  summary: string;
  entities_found: string[];
  evidence_count: number;
  confidence: string;
}

export interface Provenance {
  knowledge_version: string;
  source: string;
}

export interface AnswerResponse {
  question: string;
  answer: AnswerBody;
  entities: { name: string; type: string; guid: string }[];
  relationships: { type: string; direction: string; target_name: string }[];
  sources: EvidenceItem[];
  provenance: Provenance;
  latency_ms: number;
}

// Knowledge Graph
export interface EntityDetail {
  guid: string;
  name: string;
  type: string;
  total_mentions: number;
  sources: string[];
  relationships: {
    type: string;
    direction: string;
    target_guid: string;
    target_name: string;
    target_type: string;
    confidence: number;
  }[];
}

export interface EntitySummary {
  name: string;
  type: string;
  guid: string;
  total_mentions: number;
}

export interface ScriptureSummary {
  id: string;
  name: string;
  type: string;
  verses: number;
  coverage: number;
  source: string;
  certification: string;
}

export interface PathResult {
  path: string[];
  path_names: string[];
  depth: number;
}

export interface GraphStats {
  entities: number;
  scriptures: number;
  edges: number;
  edge_types: number;
  node_types: number;
}

// Chat
export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface ChatCompletionsRequest {
  messages: ChatMessage[];
  model?: string;
  stream?: boolean;
  temperature?: number;
  max_tokens?: number;
}

// Auth
export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface RegisterRequest {
  username: string;
  password: string;
}

export interface UserResponse {
  username: string;
  scopes: string[];
  created_at: string;
  api_key?: string;
}

// Conversations
export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  model: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  messages?: Message[];
}

export interface Message {
  id: string;
  role: "system" | "user" | "assistant" | "tool";
  content: string;
  created_at: string;
  token_count?: number;
}

// Cache
export interface CacheStats {
  search_cache: { size: number; hits: number; misses: number };
  answer_cache: { size: number; hits: number; misses: number };
  embedding_cache: { size: number; hits: number; misses: number };
}

// Health
export interface HealthResponse {
  status: string;
  version: string;
  knowledge_version: string;
  uptime_seconds: number;
}
