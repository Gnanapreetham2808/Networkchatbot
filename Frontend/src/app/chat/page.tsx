'use client';

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/AuthProvider';
import { FiSend, FiUser, FiCpu, FiZap, FiMessageSquare, FiServer } from 'react-icons/fi';
import { motion, AnimatePresence } from 'framer-motion';
import { DeviceChip } from '@/components/ui/DeviceChip';
import MagneticButton from '@/components/ui/MagneticButton';

type ChatMessage = {
  id: string;
  sender: 'user' | 'bot';
  content: string;
  timestamp: Date;
};

type Device = {
  alias: string;
  host: string;
};

const AVAILABLE_DEVICES: Device[] = [
  { alias: 'INVIJB1C01', host: '192.168.10.1' },
  { alias: 'UKLONB10C01', host: '192.168.30.1' },
  { alias: 'INVIJB10A01', host: '192.168.50.3' },
];

export default function ChatPage() {
  const router = useRouter();
  const { user, loading, idToken } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string>('');
  const [currentDevice, setCurrentDevice] = useState<{ alias?: string; host?: string } | null>(null);
  const [hasFirstResponse, setHasFirstResponse] = useState(false);
  const [agenticMode, setAgenticMode] = useState(false); // Toggle for Agentic Mode
  const [showDeviceSelector, setShowDeviceSelector] = useState(false);
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
      // Check if message is a VLAN creation request (only in Agentic Mode)
      const vlanMatch = trimmed.match(/create vlan|add vlan|new vlan|configure vlan/i);
      
      if (agenticMode && vlanMatch) {
        // VLAN automation is currently disabled
        const botText = `⚠️ Agentic Mode (VLAN Automation) is currently disabled.\n\nThis feature is under development. The system will operate in Read-Only mode for now.\n\nYou can still use show commands to query network devices.`;

        const botMessage: ChatMessage = {
          id: Date.now().toString(),
          sender: 'bot',
          content: botText,
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, botMessage]);
        setIsLoading(false);
        return;
      }

      // Default chat flow for non-VLAN commands
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
      <div className="w-full max-w-3xl bg-white dark:bg-gray-900 rounded-2xl shadow-xl flex flex-col overflow-hidden border border-gray-200 dark:border-gray-700" style={{ height: '85vh' }}>
        {/* Header with Toggle */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
          <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
            Network Chatbot
          </h1>
          
          <div className="flex items-center gap-4">
            {/* Agentic Mode Toggle */}
            <div className="flex items-center gap-2">
              <motion.button
                onClick={() => setAgenticMode(!agenticMode)}
                className={`relative flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-all duration-300 ${
                  agenticMode
                    ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg shadow-purple-500/50'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                }`}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                {agenticMode ? (
                  <>
                    <FiZap className="w-4 h-4" />
                    <span>Agentic Mode</span>
                  </>
                ) : (
                  <>
                    <FiMessageSquare className="w-4 h-4" />
                    <span>Normal Mode</span>
                  </>
                )}
              </motion.button>
              
              {/* Mode Indicator Badge */}
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className={`px-2 py-1 rounded-full text-xs font-semibold ${
                  agenticMode
                    ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300'
                    : 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300'
                }`}
              >
                {agenticMode ? 'VLAN Config' : 'Read Only'}
              </motion.div>
            </div>
            
            {/* Device Selector Button */}
            <button
              onClick={() => setShowDeviceSelector(!showDeviceSelector)}
              className="px-3 py-1.5 text-sm font-medium rounded-lg border-2 transition-all duration-200 flex items-center gap-2 hover:scale-105 bg-white dark:bg-gray-800 border-blue-300 dark:border-blue-700 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30"
              title="Select Device"
            >
              <FiServer size={16} />
              <span>Select Device</span>
            </button>
            
            {/* Device Info - Always show when available */}
            {currentDevice && (
              <DeviceChip alias={currentDevice.alias} host={currentDevice.host} />
            )}
          </div>
        </div>

        {/* Device Selector Dropdown */}
        <AnimatePresence>
          {showDeviceSelector && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/10 dark:to-indigo-900/10"
            >
              <div className="px-6 py-4">
                <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
                  <FiServer className="text-blue-600 dark:text-blue-400" />
                  Select Target Device
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                  {AVAILABLE_DEVICES.map((device) => (
                    <button
                      key={device.alias}
                      onClick={() => {
                        setCurrentDevice(device);
                        setShowDeviceSelector(false);
                      }}
                      className={`p-3 rounded-lg border-2 transition-all duration-200 text-left hover:scale-105 ${
                        currentDevice?.alias === device.alias
                          ? 'border-blue-500 bg-blue-100 dark:bg-blue-900/30 shadow-md'
                          : 'border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:border-blue-400 dark:hover:border-blue-600'
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <FiServer className={currentDevice?.alias === device.alias ? 'text-blue-600' : 'text-gray-500'} />
                        <span className="font-semibold text-sm text-gray-900 dark:text-gray-100">
                          {device.alias}
                        </span>
                      </div>
                      <div className="font-mono text-xs text-gray-600 dark:text-gray-400 ml-5">
                        {device.host}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Device Info Bar - Below header for visibility */}
        {currentDevice && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="px-4 py-2 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-b border-blue-200 dark:border-blue-800 flex items-center justify-between"
          >
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Connected Device
                </span>
              </div>
              <div className="text-sm text-gray-600 dark:text-gray-400">
                <span className="font-semibold text-blue-600 dark:text-blue-400">{currentDevice.alias}</span>
                {currentDevice.host && (
                  <>
                    <span className="mx-2">•</span>
                    <span className="font-mono text-xs bg-white dark:bg-gray-800 px-2 py-1 rounded border border-gray-300 dark:border-gray-600">
                      {currentDevice.host}
                    </span>
                  </>
                )}
              </div>
            </div>
          </motion.div>
        )}

        {/* Chat messages */}
        <div className="flex-1 px-6 py-5 space-y-5 overflow-y-auto bg-white dark:bg-gray-900 transition-colors">
          {messages.length === 0 && !isLoading && (
            <div className="flex flex-col items-center justify-center h-full text-center text-gray-400 dark:text-gray-500 px-4">
              {agenticMode ? (
                <>
                  <FiZap size={48} className="mb-3 text-purple-500 opacity-50" />
                  <p className="text-lg font-medium mb-1 text-purple-600 dark:text-purple-400">
                    Agentic Mode (Currently Disabled) ⚡
                  </p>
                  <p className="mb-2">VLAN automation features are under development</p>
                  <p className="text-sm text-gray-500">
                    The system operates in <span className="text-blue-500 font-semibold">Read-Only mode</span> for now
                  </p>
                  <div className="mt-4 px-4 py-2 bg-orange-100 dark:bg-orange-900/30 rounded-lg text-xs text-orange-700 dark:text-orange-300">
                    ⚠️ Agentic features are temporarily disabled. Use show commands only.
                  </div>
                </>
              ) : (
                <>
                  <FiCpu size={48} className="mb-3" />
                  <p className="text-lg font-medium mb-1">Welcome to Network ChatOps</p>
                  <p className="mb-2">Start chatting below 👇</p>
                  <p className="text-sm">
                    Example: <span className="text-blue-500">"Show VLANs"</span> or{' '}
                    <span className="text-gray-500">"Show interfaces"</span>
                  </p>
                  <div className="mt-4 px-4 py-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg text-xs text-blue-700 dark:text-blue-300">
                    💡 Read-Only Mode Active - Query network devices safely
                  </div>
                </>
              )}
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
          className={`flex gap-3 p-4 border-t border-gray-200 dark:border-gray-700 ${
            agenticMode
              ? 'bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20'
              : 'bg-white dark:bg-gray-900'
          }`}
        >
          <input
            type="text"
            placeholder={
              agenticMode
                ? "Configure network (e.g., 'Create VLAN 30 in core')..."
                : "Ask a network command (e.g., 'Show VLANs')..."
            }
            value={input}
            onChange={(e) => setInput(e.target.value)}
            className={`flex-1 px-4 py-2 rounded-full text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 border focus:ring-2 focus:outline-none transition-all ${
              agenticMode
                ? 'bg-purple-100 dark:bg-purple-900/30 border-purple-300 dark:border-purple-700 focus:ring-purple-400'
                : 'bg-gray-100 dark:bg-gray-800 border-gray-300 dark:border-gray-700 focus:ring-blue-400'
            }`}
            disabled={isLoading}
          />
          <MagneticButton
            type="submit"
            disabled={!input.trim() || isLoading}
            className={`w-12 h-12 rounded-full flex items-center justify-center transition ${
              !input.trim() || isLoading
                ? 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
                : agenticMode
                ? 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white shadow-lg shadow-purple-500/50'
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
