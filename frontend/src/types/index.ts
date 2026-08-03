// Message types for the chat system

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: number;
  isStreaming?: boolean;
}

export interface ChatHistory {
  role: 'user' | 'assistant';
  content: string;
}

export interface Source {
  source?: string;
  title?: string;
  url?: string;
  similarity?: number;
}

export interface Metadata {
  mode?: 'resume' | 'search';
  engine?: string;
  sources?: Source[];
  similarity?: number;
}

export interface SSEEvent {
  event: string;
  data: string;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
}

export type AgentMode = 'auto' | 'resume' | 'search';
