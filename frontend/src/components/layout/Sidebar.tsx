import React, { useState, useEffect } from 'react';
import type { Conversation } from '../../types';
import { MessageSquare, Trash2, X, Download, FileText } from 'lucide-react';

interface SidebarProps {
  conversations: Conversation[];
  currentConvId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onNewChat: () => void;
  isOpen: boolean;
  onClose: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  conversations,
  currentConvId,
  onSelect,
  onDelete,
  onNewChat,
  isOpen,
  onClose,
}) => {
  const [pdfFiles, setPdfFiles] = useState<string[]>([]);

  useEffect(() => {
    fetch('/api/pdf/list')
      .then((r) => r.json())
      .then((d) => setPdfFiles(d.files || []))
      .catch(() => {});
  }, []);

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/30 z-40 lg:hidden"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-surface-50 border-r border-surface-200 flex flex-col transition-transform duration-200
          ${isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        {/* Header */}
        <div className="h-12 border-b border-surface-200 flex items-center justify-between px-4 flex-shrink-0">
          <h3 className="text-sm font-semibold text-gray-700">对话历史</h3>
          <button
            onClick={onClose}
            className="w-7 h-7 flex items-center justify-center rounded-lg hover:bg-surface-200 transition-colors text-gray-400 lg:hidden"
          >
            <X size={16} />
          </button>
        </div>

        {/* New Chat button */}
        <div className="p-3">
          <button
            onClick={() => { onNewChat(); onClose(); }}
            className="w-full flex items-center gap-2 text-sm text-gray-600 hover:text-primary-600 bg-white hover:bg-primary-50 border border-surface-200 hover:border-primary-200 rounded-lg px-3 py-2 transition-colors"
          >
            <MessageSquare size={16} />
            新建对话
          </button>
        </div>

        {/* Conversation list */}
        <div className="flex-1 overflow-y-auto px-3 pb-3">
          {conversations.length === 0 ? (
            <p className="text-xs text-gray-400 text-center py-8">暂无对话</p>
          ) : (
            <div className="space-y-0.5">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => { onSelect(conv.id); onClose(); }}
                  className={`group flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer transition-colors text-sm
                    ${conv.id === currentConvId
                      ? 'bg-primary-50 text-primary-700 font-medium'
                      : 'text-gray-600 hover:bg-surface-200'
                    }`}
                >
                  <MessageSquare size={14} className="flex-shrink-0 opacity-50" />
                  <span className="flex-1 truncate text-xs">{conv.title}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDelete(conv.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-red-500 transition-all p-0.5"
                    title="删除"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Download Resume */}
        {pdfFiles.length > 0 && (
          <div className="border-t border-surface-200 px-3 py-3">
            <p className="text-[10px] font-medium text-gray-500 uppercase tracking-wider mb-2 px-1">
              下载简历
            </p>
            <div className="space-y-1">
              {pdfFiles.map((file) => (
                <a
                  key={file}
                  href={`/api/pdf/download/${encodeURIComponent(file)}`}
                  download={file}
                  className="flex items-center gap-2 text-xs text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded-lg px-2 py-1.5 transition-colors group"
                >
                  <FileText size={13} className="flex-shrink-0 text-gray-400 group-hover:text-primary-500" />
                  <span className="flex-1 truncate">{file.replace('.pdf', '')}</span>
                  <Download size={13} className="flex-shrink-0 opacity-0 group-hover:opacity-100 text-primary-500 transition-opacity" />
                </a>
              ))}
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="px-4 py-3 border-t border-surface-200 text-[10px] text-gray-400">
          AI Personal Agent v1.0
        </div>
      </aside>
    </>
  );
};
