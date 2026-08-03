import React from 'react';
import type { Metadata } from '../../types';
import { FileText, Search, Wifi, WifiOff, Loader2 } from 'lucide-react';

interface StatusBarProps {
  metadata: Metadata | null;
  isLoading: boolean;
  backendStatus: 'connected' | 'disconnected' | 'checking';
}

export const StatusBar: React.FC<StatusBarProps> = ({ metadata, isLoading, backendStatus }) => {
  const modeBadge = () => {
    if (!metadata?.mode) return null;
    if (metadata.mode === 'resume') {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">
          <FileText size={11} />
          RAG
        </span>
      );
    }
    if (metadata.mode === 'search') {
      return (
        <span className="inline-flex items-center gap-1 text-[11px] text-green-600 bg-green-50 px-2 py-0.5 rounded-full">
          <Search size={11} />
          {metadata.engine === 'llm_direct' ? 'LLM' : metadata.engine === 'duckduckgo' ? 'DDG' : 'Web'}
        </span>
      );
    }
    return null;
  };

  return (
    <div className="flex items-center gap-2 px-4 py-1 bg-surface-50 border-b border-surface-100 text-[11px] text-gray-400">
      {/* Backend status */}
      <div className="flex items-center gap-1">
        {backendStatus === 'checking' ? (
          <Loader2 size={11} className="animate-spin" />
        ) : backendStatus === 'connected' ? (
          <Wifi size={11} className="text-green-500" />
        ) : (
          <WifiOff size={11} className="text-red-400" />
        )}
        <span>{backendStatus === 'connected' ? '已连接' : backendStatus === 'checking' ? '检测中...' : '离线'}</span>
      </div>

      <span className="text-surface-300">|</span>

      {/* Agent mode */}
      <div className="flex items-center gap-1">
        {modeBadge() || <span>Auto</span>}
      </div>

      {/* Streaming indicator */}
      {isLoading && (
        <>
          <span className="text-surface-300">|</span>
          <span className="inline-flex items-center gap-1 text-primary-500">
            <Loader2 size={11} className="animate-spin" />
            生成中
          </span>
        </>
      )}
    </div>
  );
};
