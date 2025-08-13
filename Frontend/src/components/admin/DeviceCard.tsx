export function DeviceCard({ name, status }: { name: string; status: string }) {
  return (
    <div className="p-4 border rounded shadow-sm bg-white">
      <h3 className="font-semibold">{name}</h3>
      <p className={`text-sm ${status === 'online' ? 'text-green-600' : 'text-red-600'}`}>{status}</p>
    </div>
  );
}
