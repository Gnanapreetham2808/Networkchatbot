export function AuditLog({ logs }: { logs: string[] }) {
  return (
    <div className="space-y-1">
      {logs.map((log, i) => (
        <div key={i} className="text-sm text-gray-600">{log}</div>
      ))}
    </div>
  );
}
