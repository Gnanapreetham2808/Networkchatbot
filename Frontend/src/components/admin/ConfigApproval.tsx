export function ConfigApproval({ onApprove }: { onApprove: () => void }) {
  return (
    <div className="p-4 border rounded space-y-2">
      <p>New configuration detected. Approve changes?</p>
      <button onClick={onApprove} className="bg-green-500 text-white px-4 py-2 rounded">Approve</button>
    </div>
  );
}
