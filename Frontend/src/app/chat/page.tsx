'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/AuthProvider';
import { FiSend, FiUser, FiCpu } from 'react-icons/fi';
import { motion, AnimatePresence } from 'framer-motion';
import { DeviceChip } from '@/components/ui/DeviceChip';
import MagneticButton from '@/components/ui/MagneticButton';

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
  const [sessionId, setSessionId] = useState<string>('');
  const [currentDevice, setCurrentDevice] = useState<{ alias?: string; host?: string } | null>(null);
  const [hasFirstResponse, setHasFirstResponse] = useState(false);
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

  // Ensure a stable session_id across requests
  useEffect(() => {
    try {
      const key = 'netops_session_id';
      let sid = localStorage.getItem(key);
      if (!sid) {
        sid = crypto.randomUUID();
        localStorage.setItem(key, sid);
      }
      setSessionId(sid);
    } catch (e) {
      // Fallback if crypto/localStorage unavailable
      setSessionId(String(Date.now()));
    }
  }, []);

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
        body: JSON.stringify({ session_id: sessionId, query: trimmed })
      });

      let botText = '';
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        botText = `Error: ${err.error || res.status}`;
      } else {
        const data = await res.json();
        botText = data.output || data.warning || data.raw_output || JSON.stringify(data, null, 2);
        if (data.device_alias || data.device_host) {
          setCurrentDevice({ alias: data.device_alias, host: data.device_host });
          if (!hasFirstResponse) setHasFirstResponse(true);
        }
        if (data.session_id && data.session_id !== sessionId) {
          setSessionId(data.session_id);
          try { localStorage.setItem('netops_session_id', data.session_id); } catch {}
        }
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
    <div className="min-h-screen flex items-center justify-center px-4 py-10 bg-[#f5f7fa] dark:bg-gray-950 transition-colors">
      <div className="w-full max-w-3xl bg-white dark:bg-gray-900 rounded-2xl shadow-xl flex flex-col overflow-hidden border border-gray-200 dark:border-gray-700">
        {/* Header */}
  <div className="bg-blue-700 dark:bg-blue-600 px-6 py-4 text-lg font-semibold text-white border-b border-blue-800/40 dark:border-blue-500/40 flex items-center justify-between gap-3">
          <span>💬 Network Assistant</span>
          <DeviceChip alias={currentDevice?.alias} host={currentDevice?.host} loading={!hasFirstResponse} />
        </div>

        {/* Chat messages */}
  <div className="flex-1 px-6 py-5 space-y-5 overflow-y-auto max-h-[65vh] bg-white dark:bg-gray-900 transition-colors">
          {messages.length === 0 && !isLoading && (
            <div className="text-center text-gray-400 dark:text-gray-500 py-16">
              <p className="mb-2">Start chatting below 👇</p>
              <p className="text-sm">
                Example: <span className="text-blue-500">"Show VLANs"</span>
              </p>
            </div>
          )}

          <AnimatePresence initial={false}>
            {messages.map((msg) => (
              <motion.div
                key={msg.id}
                className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                initial={{ opacity: 0, y: 8, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -8, scale: 0.98 }}
                transition={{ type: 'spring', stiffness: 260, damping: 22 }}
              >
                <div
                  className={`rounded-xl px-4 py-3 text-sm whitespace-pre-wrap max-w-xs shadow-md ${
                    msg.sender === 'user'
                      ? 'bg-emerald-500 text-white rounded-br-none'
                      : 'bg-blue-100 dark:bg-blue-900/40 text-gray-800 dark:text-gray-100 rounded-bl-none'
                  }`}
                >
                  <div className="text-xs opacity-60 mb-1 flex items-center gap-1">
                    {msg.sender === 'user' ? <FiUser size={14} /> : <FiCpu size={14} />}
                    {formatTime(msg.timestamp)}
                  </div>
                  {msg.content}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {isLoading && (
            <div className="flex justify-start">
              <motion.div
                className="bg-blue-100 dark:bg-blue-900/40 text-gray-800 dark:text-gray-100 px-4 py-3 rounded-xl text-sm shadow"
                initial={{ opacity: 0.6 }}
                animate={{ opacity: [0.6, 1, 0.6] }}
                transition={{ duration: 1.2, repeat: Infinity }}
              >
                Bot is typing...
              </motion.div>
            </div>
          )}

          <div ref={endRef} />
        </div>

        {/* Input area */}
        <form
          onSubmit={handleSend}
          className="flex gap-3 p-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900"
        >
          <input
            type="text"
            placeholder="Ask a network command..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className="flex-1 px-4 py-2 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 border border-gray-300 dark:border-gray-700 focus:ring-2 focus:ring-blue-400 focus:outline-none"
            disabled={isLoading}
          />
          <MagneticButton
            type="submit"
            disabled={!input.trim() || isLoading}
            className={`w-12 h-12 rounded-full flex items-center justify-center transition ${
              !input.trim() || isLoading
                ? 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                : 'bg-emerald-500 hover:bg-emerald-600 dark:hover:bg-emerald-500 text-white'
            }`}
          >
            <FiSend />
          </MagneticButton>
        </form>
      </div>
    </div>
  );
}
