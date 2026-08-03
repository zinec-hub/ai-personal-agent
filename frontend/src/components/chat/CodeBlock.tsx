import React, { useState } from 'react';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneLight } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check } from 'lucide-react';

interface CodeBlockProps {
  language?: string;
  value?: string;
  children?: string;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({ language, value, children }) => {
  const [copied, setCopied] = useState(false);
  const code = value || children || '';
  const lang = language || '';

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group my-3 rounded-lg overflow-hidden border border-surface-200">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-1.5 bg-surface-100 text-xs text-gray-500 font-medium">
        <span>{lang || 'text'}</span>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity hover:text-primary-600"
        >
          {copied ? (
            <Check size={14} className="text-green-500" />
          ) : (
            <Copy size={14} />
          )}
          <span>{copied ? 'Copied!' : 'Copy'}</span>
        </button>
      </div>
      <SyntaxHighlighter
        language={lang || 'text'}
        style={oneLight}
        customStyle={{
          margin: 0,
          padding: '1rem',
          fontSize: '0.8125rem',
          lineHeight: '1.6',
          background: '#fafbfc',
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
};
