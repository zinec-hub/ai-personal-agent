import React from 'react';
import { Sparkles, FileText, Globe, MessageSquare } from 'lucide-react';
import { Card } from '../common/Card';

interface WelcomeScreenProps {
  appName: string;
  welcomeMessage: string;
  suggestions: string[];
  onSuggestionClick: (suggestion: string) => void;
}

const featureCards = [
  {
    icon: FileText,
    title: '简历问答',
    description: '基于您的简历文档，智能回答相关问题，如教育背景、技能特长、工作经验等。',
    color: 'text-blue-500',
    bg: 'bg-blue-50',
  },
  {
    icon: Globe,
    title: '联网搜索',
    description: '自动联网检索最新信息，支持多搜索引擎聚合，确保信息准确可靠。',
    color: 'text-green-500',
    bg: 'bg-green-50',
  },
  {
    icon: Sparkles,
    title: '智能路由',
    description: '自动判断问题类型：简历问题走 RAG 检索，通用问题走联网搜索。',
    color: 'text-purple-500',
    bg: 'bg-purple-50',
  },
];

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({
  appName,
  welcomeMessage,
  suggestions,
  onSuggestionClick,
}) => {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-4 py-8 overflow-y-auto">
      {/* Hero */}
      <div className="text-center mb-8 animate-fade-in">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-primary-500 to-purple-500 text-white mb-4 shadow-lg">
          <MessageSquare size={28} />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">{appName}</h1>
        <p className="text-sm text-gray-500 max-w-md">{welcomeMessage}</p>
      </div>

      {/* Feature Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 w-full max-w-2xl mb-8 animate-slide-up">
        {featureCards.map((card) => (
          <Card key={card.title} padding="md" className="hover:shadow-md transition-shadow">
            <div className={`w-9 h-9 rounded-lg ${card.bg} flex items-center justify-center mb-2`}>
              <card.icon size={18} className={card.color} />
            </div>
            <h3 className="text-sm font-semibold text-gray-800 mb-1">{card.title}</h3>
            <p className="text-xs text-gray-500 leading-relaxed">{card.description}</p>
          </Card>
        ))}
      </div>

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <div className="w-full max-w-md animate-slide-up" style={{ animationDelay: '0.15s' }}>
          <p className="text-xs text-gray-400 mb-3 text-center">试试这些问题</p>
          <div className="flex flex-wrap gap-2 justify-center">
            {suggestions.map((s, i) => (
              <button
                key={i}
                onClick={() => onSuggestionClick(s)}
                className="px-3.5 py-1.5 text-xs bg-surface-50 hover:bg-surface-100 border border-surface-200 rounded-full text-gray-600 hover:text-primary-600 hover:border-primary-200 transition-colors"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
