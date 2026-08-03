import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { ChatWindow } from './components/chat/ChatWindow';
import { InputBox } from './components/chat/InputBox';
import { StatusBar } from './components/chat/StatusBar';
import { useChat } from './hooks/useChat';
import { fetchConfig } from './api/chat';
import type { AgentMode } from './types';

const App: React.FC = () => {
  const {
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
  } = useChat();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [backendStatus, setBackendStatus] = useState<'connected' | 'disconnected' | 'checking'>('checking');
  const [config, setConfig] = useState({
    appName: 'AI Personal Agent',
    welcomeMessage: 'Hello! I am your AI assistant.',
    suggestions: [] as string[],
  });

  // Fetch config and check backend health
  useEffect(() => {
    fetchConfig().then(setConfig).catch(console.error);

    const checkHealth = async () => {
      try {
        const resp = await fetch('/api/health');
        if (resp.ok) {
          setBackendStatus('connected');
        } else {
          setBackendStatus('disconnected');
        }
      } catch {
        setBackendStatus('disconnected');
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleSend = useCallback(
    (message: string, mode: AgentMode) => {
      sendMessage(message, mode);
    },
    [sendMessage]
  );

  const handleSuggestionClick = useCallback(
    (suggestion: string) => {
      sendMessage(suggestion, 'auto');
    },
    [sendMessage]
  );

  const currentTitle = currentConv?.title || config.appName;

  return (
    <div className="h-screen flex flex-col bg-white">
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar */}
        <Sidebar
          conversations={conversations}
          currentConvId={currentConv?.id || null}
          onSelect={switchConversation}
          onDelete={deleteConversation}
          onNewChat={newConversation}
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        {/* Main area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Header */}
          <Header
            onNewChat={newConversation}
            onToggleSidebar={() => setSidebarOpen(true)}
            title={currentTitle}
          />

          {/* Status bar */}
          <StatusBar
            metadata={metadata}
            isLoading={isLoading}
            backendStatus={backendStatus}
          />

          {/* Chat area */}
          <ChatWindow
            messages={messages}
            isLoading={isLoading}
            metadata={metadata}
            appName={config.appName}
            welcomeMessage={config.welcomeMessage}
            suggestions={config.suggestions}
            onSuggestionClick={handleSuggestionClick}
          />

          {/* Input */}
          <InputBox
            onSend={handleSend}
            onStop={stopStreaming}
            isLoading={isLoading}
          />
        </div>
      </div>
    </div>
  );
};

export default App;
