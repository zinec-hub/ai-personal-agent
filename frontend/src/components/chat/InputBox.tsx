import React, { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { Send, Square, Search, FileText, ChevronDown } from 'lucide-react';
import type { AgentMode } from '../../types';

interface InputBoxProps {
  onSend: (message: string, mode: AgentMode) => void;
  onStop: () => void;
  isLoading: boolean;
}

const modeOptions: { value: AgentMode; label: string; icon: React.ReactNode }[] = [
  { value: 'auto', label: 'Auto', icon: null },
  { value: 'resume', label: 'Resume', icon: <FileText size={14} /> },
  { value: 'search', label: 'Search', icon: <Search size={14} /> },
];

export const InputBox: React.FC<InputBoxProps> = ({ onSend, onStop, isLoading }) => {
  const [input, setInput] = useState('');
  const [mode, setMode] = useState<AgentMode>('auto');
  const [showModeMenu, setShowModeMenu] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = Math.min(el.scrollHeight, 160) + 'px';
    }
  }, [input]);

  // Close mode menu on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setShowModeMenu(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed, mode);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const currentMode = modeOptions.find((m) => m.value === mode);

  return (
    <div className="border-t border-surface-200 bg-white px-4 py-3">
      <div className="max-w-3xl mx-auto">
        <div className="flex items-end gap-2 bg-surface-50 border border-surface-200 rounded-2xl px-4 py-2 focus-within:border-primary-300 focus-within:ring-2 focus-within:ring-primary-50 transition-all">
          {/* Mode selector */}
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setShowModeMenu(!showModeMenu)}
              className="flex items-center gap-1 text-xs text-gray-400 hover:text-primary-600 transition-colors py-1 px-1"
              title="切换模式"
            >
              {currentMode?.icon}
              <span className="font-medium">{currentMode?.label}</span>
              <ChevronDown size={12} />
            </button>
            {showModeMenu && (
              <div className="absolute bottom-full left-0 mb-1 bg-white border border-surface-200 rounded-lg shadow-lg py-1 min-w-[120px] z-50">
                {modeOptions.map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => {
                      setMode(opt.value);
                      setShowModeMenu(false);
                    }}
                    className={`flex items-center gap-2 w-full px-3 py-1.5 text-xs hover:bg-surface-50 transition-colors
                      ${mode === opt.value ? 'text-primary-600 font-medium bg-primary-50' : 'text-gray-600'}`}
                  >
                    {opt.icon}
                    <span>{opt.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入你的问题..."
            rows={1}
            className="flex-1 bg-transparent resize-none text-sm text-gray-800 placeholder-gray-400 outline-none py-1.5 max-h-40"
            disabled={isLoading}
          />

          {/* Send / Stop button */}
          {isLoading ? (
            <button
              onClick={onStop}
              className="flex-shrink-0 w-8 h-8 bg-red-500 hover:bg-red-600 text-white rounded-full flex items-center justify-center transition-colors"
              title="停止"
            >
              <Square size={14} fill="white" />
            </button>
          ) : (
            <button
              onClick={handleSend}
              disabled={!input.trim()}
              className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center transition-colors
                ${input.trim()
                  ? 'bg-primary-600 text-white hover:bg-primary-700'
                  : 'bg-surface-200 text-gray-400 cursor-not-allowed'
                }`}
              title="发送"
            >
              <Send size={14} />
            </button>
          )}
        </div>

        <p className="text-[10px] text-gray-400 text-center mt-2">
          按 Enter 发送，Shift+Enter 换行
        </p>
      </div>
    </div>
  );
};
