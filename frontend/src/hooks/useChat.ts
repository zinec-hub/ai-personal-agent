import { useState, useCallback, useRef } from 'react';
import type { Message, Conversation, ChatHistory, AgentMode, Metadata } from '../types';
import { streamChat } from '../api/chat';

let nextId = 1;
function genId(): string {
  return `msg_${Date.now()}_${nextId++}`;
}

function genConvId(): string {
  return `conv_${Date.now()}`;
}

export function useChat() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConvId, setCurrentConvId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [metadata, setMetadata] = useState<Metadata | null>(null);
  const cancelRef = useRef<(() => void) | null>(null);

  const currentConv = conversations.find((c) => c.id === currentConvId) || null;

  const messages = currentConv?.messages || [];

  const sendMessage = useCallback(
    (content: string, mode: AgentMode = 'auto') => {
      let convId = currentConvId;

      // Create a new conversation if needed
      if (!convId) {
        convId = genConvId();
        const newConv: Conversation = {
          id: convId,
          title: content.slice(0, 30) + (content.length > 30 ? '...' : ''),
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now(),
        };
        setConversations((prev) => [newConv, ...prev]);
        setCurrentConvId(convId);
      }

      const userMsg: Message = {
        id: genId(),
        role: 'user',
        content,
        timestamp: Date.now(),
      };

      const assistantMsg: Message = {
        id: genId(),
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
        isStreaming: true,
      };

      // Add messages
      setConversations((prev) =>
        prev.map((c) => {
          if (c.id !== convId) return c;
          return {
            ...c,
            messages: [...c.messages, userMsg, assistantMsg],
            updatedAt: Date.now(),
            title: c.messages.length === 0
              ? content.slice(0, 30) + (content.length > 30 ? '...' : '')
              : c.title,
          };
        })
      );

      setIsLoading(true);
      setMetadata(null);

      // Build history
      const currentMessages = conversations.find((c) => c.id === convId)?.messages || [];
      const history: ChatHistory[] = currentMessages
        .filter((m) => !m.isStreaming && m.role !== 'system')
        .map((m) => ({ role: m.role as 'user' | 'assistant', content: m.content }));

      const cancel = streamChat(
        content,
        {
          onDelta: (text) => {
            setConversations((prev) =>
              prev.map((c) => {
                if (c.id !== convId) return c;
                return {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === assistantMsg.id
                      ? { ...m, content: m.content + text }
                      : m
                  ),
                  updatedAt: Date.now(),
                };
              })
            );
          },
          onMetadata: (meta: Record<string, unknown>) => {
            setMetadata(meta as unknown as Metadata);
          },
          onDone: () => {
            setConversations((prev) =>
              prev.map((c) => {
                if (c.id !== convId) return c;
                return {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === assistantMsg.id
                      ? { ...m, isStreaming: false }
                      : m
                  ),
                  updatedAt: Date.now(),
                };
              })
            );
            setIsLoading(false);
          },
          onError: (error: string) => {
            setConversations((prev) =>
              prev.map((c) => {
                if (c.id !== convId) return c;
                return {
                  ...c,
                  messages: c.messages.map((m) =>
                    m.id === assistantMsg.id
                      ? { ...m, content: `Error: ${error}`, isStreaming: false }
                      : m
                  ),
                  updatedAt: Date.now(),
                };
              })
            );
            setIsLoading(false);
          },
        },
        {
          history,
          mode,
        }
      );

      cancelRef.current = cancel;
    },
    [currentConvId, conversations]
  );

  const stopStreaming = useCallback(() => {
    cancelRef.current?.();
    setIsLoading(false);
    setConversations((prev) =>
      prev.map((c) => {
        if (c.id !== currentConvId) return c;
        return {
          ...c,
          messages: c.messages.map((m) =>
            m.isStreaming ? { ...m, isStreaming: false, content: m.content + '\n\n*[已停止]*' } : m
          ),
        };
      })
    );
  }, [currentConvId]);

  const newConversation = useCallback(() => {
    setCurrentConvId(null);
    setMetadata(null);
  }, []);

  const switchConversation = useCallback((id: string) => {
    setCurrentConvId(id);
    setMetadata(null);
  }, []);

  const deleteConversation = useCallback((id: string) => {
    setConversations((prev) => prev.filter((c) => c.id !== id));
    if (currentConvId === id) {
      setCurrentConvId(null);
      setMetadata(null);
    }
  }, [currentConvId]);

  return {
    conversations,
    currentConv,
    messages,
    isLoading,
    metadata,
    sendMessage,
    stopStreaming,
    newConversation,
    switchConversation,
    deleteConversation,
  };
}
