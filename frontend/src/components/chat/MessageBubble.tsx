import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Message } from '../../types';
import { CodeBlock } from './CodeBlock';
import { Bot, User } from 'lucide-react';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <div className="flex justify-center my-2">
        <span className="text-xs text-gray-400 bg-surface-100 px-3 py-1 rounded-full">
          {message.content}
        </span>
      </div>
    );
  }

  return (
    <div
      className={`flex gap-3 animate-fade-in ${
        isUser ? 'flex-row-reverse' : 'flex-row'
      } mb-4`}
    >
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center
          ${isUser
            ? 'bg-primary-600 text-white'
            : 'bg-gradient-to-br from-primary-500 to-purple-500 text-white'
          }`}
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>

      {/* Content */}
      <div
        className={`max-w-[75%] min-w-0 ${
          isUser
            ? 'bg-primary-600 text-white rounded-2xl rounded-tr-md px-4 py-2.5'
            : 'prose prose-sm prose-gray max-w-none'
        }`}
      >
        {isUser ? (
          <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
        ) : (
          <div className="animate-fade-in">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  // Check if it's an inline code block by inspecting the node
                  const value = String(children).replace(/\n$/, '');
                  const isInline = !match && !value.includes('\n');
                  if (isInline) {
                    return (
                      <code className="px-1.5 py-0.5 text-xs bg-surface-100 text-primary-700 rounded font-mono" {...props}>
                        {children}
                      </code>
                    );
                  }
                  return (
                    <CodeBlock language={match?.[1]} value={value} />
                  );
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
              {message.content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
};
