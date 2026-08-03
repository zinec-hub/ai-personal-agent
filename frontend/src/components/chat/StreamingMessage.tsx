import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { CodeBlock } from './CodeBlock';
import { Bot } from 'lucide-react';

interface StreamingMessageProps {
  content: string;
}

export const StreamingMessage: React.FC<StreamingMessageProps> = ({ content }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll
  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [content]);

  return (
    <div className="flex gap-3 mb-4 animate-fade-in" ref={scrollRef}>
      {/* Avatar */}
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-purple-500 text-white flex items-center justify-center">
        <Bot size={16} />
      </div>

      {/* Content */}
      <div className="max-w-[75%] min-w-0 prose prose-sm prose-gray max-w-none">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            code({ className, children, ...props }) {
              const match = /language-(\w+)/.exec(className || '');
              const value = String(children).replace(/\n$/, '');
              const isInline = !match && !value.includes('\n');
              if (isInline) {
                return (
                  <code className="px-1.5 py-0.5 text-xs bg-surface-100 text-primary-700 rounded font-mono" {...props}>
                    {children}
                  </code>
                );
              }
              return <CodeBlock language={match?.[1]} value={value} />;
            },
            pre({ children }) {
              return <>{children}</>;
            },
            table({ children }) {
              return (
                <div className="overflow-x-auto my-3">
                  <table className="min-w-full border-collapse border border-surface-200 text-sm">
                    {children}
                  </table>
                </div>
              );
            },
            th({ children }) {
              return (
                <th className="border border-surface-200 px-3 py-2 bg-surface-50 font-semibold text-left">
                  {children}
                </th>
              );
            },
            td({ children }) {
              return (
                <td className="border border-surface-200 px-3 py-2">{children}</td>
              );
            },
            a({ href, children }) {
              return (
                <a href={href} target="_blank" rel="noopener noreferrer" className="text-primary-600 hover:underline">
                  {children}
                </a>
              );
            },
          }}
        >
          {content || 'thinking...'}
        </ReactMarkdown>

        {/* Typing indicator shown when content is empty */}
        {!content && (
          <div className="flex gap-1.5 items-center py-2">
            <div className="w-2 h-2 bg-primary-400 rounded-full animate-pulse-dot" style={{ animationDelay: '0s' }} />
            <div className="w-2 h-2 bg-primary-400 rounded-full animate-pulse-dot" style={{ animationDelay: '0.2s' }} />
            <div className="w-2 h-2 bg-primary-400 rounded-full animate-pulse-dot" style={{ animationDelay: '0.4s' }} />
          </div>
        )}
      </div>
    </div>
  );
};
