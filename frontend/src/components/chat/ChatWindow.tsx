import React, { useRef, useEffect } from 'react';
import type { Message, Metadata } from '../../types';
import { MessageBubble } from './MessageBubble';
import { StreamingMessage } from './StreamingMessage';
import { WelcomeScreen } from './WelcomeScreen';

interface ChatWindowProps {
  messages: Message[];
  isLoading: boolean;
  metadata: Metadata | null;
  appName: string;
  welcomeMessage: string;
  suggestions: string[];
  onSuggestionClick: (suggestion: string) => void;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  isLoading,
  metadata,
  appName,
  welcomeMessage,
  suggestions,
  onSuggestionClick,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <WelcomeScreen
        appName={appName}
        welcomeMessage={welcomeMessage}
        suggestions={suggestions}
        onSuggestionClick={onSuggestionClick}
      />
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4">
      <div className="max-w-3xl mx-auto">
        {messages.map((msg) => {
          if (msg.isStreaming) {
            return <StreamingMessage key={msg.id} content={msg.content} />;
          }
          return <MessageBubble key={msg.id} message={msg} />;
        })}

        <div ref={bottomRef} />
      </div>
    </div>
  );
};
