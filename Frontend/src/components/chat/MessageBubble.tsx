export function MessageBubble({
  sender,
  content,
}: {
  sender: 'user' | 'bot';
  content: string;
}) {
  // Alignment and colors based on sender
  const base =
    "max-w-xl p-3 rounded-2xl shadow-sm mb-2 text-base break-words";
  const userStyles =
    "bg-blue-600 text-white ml-auto mr-2 rounded-br-md rounded-tr-none";
  const botStyles =
    "bg-gray-100 text-gray-900 mr-auto ml-2 border border-gray-200 rounded-bl-md rounded-tl-none";

  return (
    <div className={`flex ${sender === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div className={`${base} ${sender === 'user' ? userStyles : botStyles}`}>
        {content}
      </div>
    </div>
  );
}
