'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/AuthProvider';
import { FiSend, FiUser, FiCpu } from 'react-icons/fi';

type ChatMessage = {
  id: string;
  sender: 'user' | 'bot';
  content: string;
  timestamp: Date;
};

export default function ChatPage() {
  const router = useRouter();
  const { user, loading, idToken } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);
  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000/api/nlp/network-command/';

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [loading, user, router]);

  const formatTime = (date: Date) =>
    date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      sender: 'user',
      content: trimmed,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (idToken) headers['Authorization'] = `Bearer ${idToken}`;
      const res = await fetch(BACKEND_URL, {
        method: 'POST',
        headers,
        body: JSON.stringify({ device_ip: '192.168.10.1', query: trimmed })
      });

      let botText = '';
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        botText = `Error: ${err.error || res.status}`;
      } else {
        const data = await res.json();
        botText = data.output || data.warning || JSON.stringify(data, null, 2);
      }

      const botMessage: ChatMessage = {
        id: Date.now().toString(),
        sender: 'bot',
        content: botText,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, botMessage]);
    } catch (err: any) {
      const botMessage: ChatMessage = {
        id: Date.now().toString(),
        sender: 'bot',
        content: `Request failed: ${err.message}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, botMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  if (loading || (!user && !loading)) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return (
    <div className="min-h-screen bg-[#f5f7fa] flex items-center justify-center px-4 py-10">
      <div className="w-full max-w-3xl bg-white rounded-2xl shadow-xl flex flex-col overflow-hidden border border-gray-200">
        {/* Header */}
        <div className="bg-blue-700 px-6 py-4 text-lg font-semibold text-white border-b">
          💬 Network Assistant
        </div>

        {/* Chat messages */}
        <div className="flex-1 px-6 py-5 space-y-5 overflow-y-auto max-h-[65vh]">
          {messages.length === 0 && !isLoading && (
            <div className="text-center text-gray-400 py-16">
              <p className="mb-2">Start chatting below 👇</p>
              <p className="text-sm">
                Example: <span className="text-blue-500">"Show VLANs"</span>
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`rounded-xl px-4 py-3 text-sm whitespace-pre-wrap max-w-xs shadow-md ${
                  msg.sender === 'user'
                    ? 'bg-emerald-500 text-white rounded-br-none'
                    : 'bg-blue-100 text-gray-800 rounded-bl-none'
                }`}
              >
                <div className="text-xs opacity-60 mb-1 flex items-center gap-1">
                  {msg.sender === 'user' ? <FiUser size={14} /> : <FiCpu size={14} />}
                  {formatTime(msg.timestamp)}
                </div>
                {msg.content}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-blue-100 text-gray-800 px-4 py-3 rounded-xl text-sm shadow">
                Bot is typing...
              </div>
            </div>
          )}

          <div ref={endRef} />
        </div>

        {/* Input area */}
        <form
          onSubmit={handleSend}
          className="flex gap-3 p-4 border-t border-gray-200 bg-white"
        >
          <input
            type="text"
            placeholder="Ask a network command..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 px-4 py-2 rounded-full bg-gray-100 text-gray-900 placeholder-gray-400 border border-gray-300 focus:ring-2 focus:ring-blue-400 focus:outline-none"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className={`w-12 h-12 rounded-full flex items-center justify-center transition ${
              !input.trim() || isLoading
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-emerald-500 hover:bg-emerald-600 text-white'
            }`}
          >
            <FiSend />
          </button>
        </form>
      </div>
    </div>
  );
}
