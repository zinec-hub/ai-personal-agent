/**
 * SSE streaming chat client.
 * Connects to the backend /api/chat endpoint and parses SSE events.
 */
import type { SSEEvent, ChatHistory, AgentMode } from '../types';

export interface ChatCallbacks {
  onDelta: (content: string) => void;
  onMetadata: (metadata: Record<string, unknown>) => void;
  onDone: () => void;
  onError: (error: string) => void;
}

export function streamChat(
  message: string,
  callbacks: ChatCallbacks,
  options?: {
    history?: ChatHistory[];
    mode?: AgentMode;
    signal?: AbortSignal;
  }
): () => void {
  const controller = new AbortController();
  const signal = options?.signal || controller.signal;

  const body: Record<string, unknown> = {
    message,
    history: options?.history || [],
    mode: options?.mode || 'auto',
  };

  fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        callbacks.onError(`HTTP ${response.status}: ${response.statusText}`);
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        callbacks.onError('No response body');
        return;
      }

      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          // Keep the last partial line in buffer
          buffer = lines.pop() || '';

          let currentEvent = '';
          for (const line of lines) {
            const trimmed = line.trim();
            if (trimmed.startsWith('event: ')) {
              currentEvent = trimmed.slice(7).trim();
            } else if (trimmed.startsWith('data: ')) {
              const data = trimmed.slice(6);
              handleEvent(currentEvent, data, callbacks);
              currentEvent = '';
            }
          }
        }
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === 'AbortError') {
          // User cancelled — not an error
          return;
        }
        callbacks.onError(err instanceof Error ? err.message : 'Stream error');
      }
    })
    .catch((err) => {
      if (err instanceof DOMException && err.name === 'AbortError') {
        return; // Cancelled
      }
      callbacks.onError(err instanceof Error ? err.message : 'Network error');
    });

  // Return cancel function
  return () => controller.abort();
}

function handleEvent(
  event: string,
  data: string,
  callbacks: ChatCallbacks
): void {
  try {
    const parsed = JSON.parse(data);

    switch (event) {
      case 'delta':
        if (parsed.content) {
          callbacks.onDelta(parsed.content);
        }
        break;
      case 'metadata':
        callbacks.onMetadata(parsed);
        break;
      case 'done':
        callbacks.onDone();
        break;
      case 'error':
        callbacks.onError(parsed.message || 'Unknown error');
        break;
    }
  } catch {
    // If JSON parse fails, treat raw data as delta
    if (event === 'delta') {
      callbacks.onDelta(data);
    }
  }
}

/**
 * Fetch public config from the backend.
 */
export async function fetchConfig(): Promise<{
  appName: string;
  welcomeMessage: string;
  suggestions: string[];
}> {
  const resp = await fetch('/api/config');
  if (!resp.ok) {
    return {
      appName: 'AI Personal Agent',
      welcomeMessage: '你好！我是你的个人 AI 助手。',
      suggestions: [],
    };
  }
  return resp.json();
}
