import React from 'react';
import type { Metadata } from '../../types';
import { FileText, Globe, Cpu, ExternalLink } from 'lucide-react';

interface ContextPanelProps {
  metadata: Metadata | null;
  isLoading: boolean;
}

export const ContextPanel: React.FC<ContextPanelProps> = ({ metadata, isLoading }) => {
  if (!metadata || !metadata.mode) return null;

  return (
    <div className="border-t border-surface-200 bg-surface-50 px-4 py-2.5 animate-fade-in">
      <div className="max-w-3xl mx-auto">
        {/* Mode info */}
        <div className="flex items-center gap-2 mb-2">
          {metadata.mode === 'resume' ? (
            <FileText size={13} className="text-blue-500" />
          ) : (
            <Globe size={13} className="text-green-500" />
          )}
          <span className="text-[11px] font-medium text-gray-600">
            {metadata.mode === 'resume'
              ? 'Resume RAG Mode'
              : `Search Mode · ${metadata.engine || 'search'}`}
          </span>
          {metadata.similarity != null && metadata.similarity > 0 && (
            <span className="text-[10px] text-gray-400 bg-white px-1.5 py-0.5 rounded border border-surface-200">
              similarity: {(metadata.similarity * 100).toFixed(0)}%
            </span>
          )}
        </div>

        {/* Sources for search mode */}
        {metadata.mode === 'search' && metadata.sources && metadata.sources.length > 0 && (
          <div className="space-y-1">
            {metadata.sources.slice(0, 5).map((s, i) => (
              <a
                key={i}
                href={s.url || '#'}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-[11px] text-gray-500 hover:text-primary-600 transition-colors group"
              >
                <ExternalLink size={10} className="flex-shrink-0" />
                <span className="truncate">{s.title}</span>
              </a>
            ))}
          </div>
        )}

        {/* Source documents for resume mode */}
        {metadata.mode === 'resume' && metadata.sources && metadata.sources.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {metadata.sources.map((s, i) => (
              <span key={i} className="text-[10px] text-blue-600 bg-blue-50 px-1.5 py-0.5 rounded border border-blue-100">
                {s.source} ({(s.similarity! * 100).toFixed(0)}%)
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
