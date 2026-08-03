import React from 'react';
import { MessageSquarePlus, Menu } from 'lucide-react';

interface HeaderProps {
  onNewChat: () => void;
  onToggleSidebar: () => void;
  title?: string;
}

export const Header: React.FC<HeaderProps> = ({ onNewChat, onToggleSidebar, title }) => {
  return (
    <header className="h-12 border-b border-surface-200 bg-white flex items-center justify-between px-4 flex-shrink-0">
      <div className="flex items-center gap-2">
        <button
          onClick={onToggleSidebar}
          className="w-8 h-8 flex items-center justify-center rounded-lg hover:bg-surface-100 transition-colors text-gray-500 lg:hidden"
        >
          <Menu size={18} />
        </button>
        <h2 className="text-sm font-semibold text-gray-800 truncate max-w-[200px]">
          {title || 'AI Personal Agent'}
        </h2>
      </div>

      <button
        onClick={onNewChat}
        className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-primary-600 hover:bg-primary-50 px-3 py-1.5 rounded-lg transition-colors"
      >
        <MessageSquarePlus size={15} />
        <span className="hidden sm:inline">新建对话</span>
      </button>
    </header>
  );
};
