import { FiCopy } from 'react-icons/fi';
import { useState } from 'react';

type CommandOutputProps = {
  content: string;
  language?: 'network' | 'json' | 'plaintext';
};

export function CommandOutput({ content, language = 'network' }: CommandOutputProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const languageClasses = {
    network: 'bg-gray-900 text-green-400 font-mono',
    json: 'bg-gray-50 border border-gray-200 text-gray-800',
    plaintext: 'bg-white border border-gray-200'
  };

  return (
    <div className="relative">
      <pre className={`p-4 rounded-lg overflow-x-auto text-sm ${languageClasses[language]}`}>
        {content}
      </pre>
      <button
        onClick={handleCopy}
        className="absolute top-2 right-2 p-2 bg-gray-800 text-white rounded hover:bg-gray-700 transition-colors"
        title="Copy to clipboard"
      >
        <FiCopy />
      </button>
      {copied && (
        <div className="absolute top-2 right-12 px-2 py-1 bg-green-600 text-white text-xs rounded">
          Copied!
        </div>
      )}
    </div>
  );
}