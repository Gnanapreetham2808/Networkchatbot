'use client';
import { FiSend } from 'react-icons/fi';

export function CommandInput({
  input,
  setInput,
  onSend,
}: {
  input: string;
  setInput: (val: string) => void;
  onSend: () => void;
}) {
  // Enable pressing Enter to send
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') onSend();
  };

  return (
    <div className="flex space-x-2 w-full max-w-xl p-2 bg-white rounded-xl shadow-md border border-gray-200">
      <input
        value={input}
        autoFocus
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        className="
          flex-1 text-base
          border-none outline-none bg-transparent
          px-4 py-2 rounded-full
          transition-colors
          placeholder-gray-400 focus:placeholder-blue-300
        "
        placeholder="Type a command..."
      />
      <button
        onClick={onSend}
        aria-label="Send command"
        className="
          flex items-center justify-center
          bg-blue-600 hover:bg-blue-700 focus:bg-blue-800
          text-white px-4 py-2 rounded-full
          transition-colors shadow
          disabled:opacity-60
        "
        disabled={!input.trim()}
      >
        <FiSend size={20} />
      </button>
    </div>
  );
}
