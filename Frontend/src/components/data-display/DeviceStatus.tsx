export function DeviceStatus({ status }: { status: string }) {
  const color = status === 'online' ? 'green' : 'red';
  return (
    <div className={`text-${color}-600 font-bold`}>
      {status.toUpperCase()}
    </div>
  );
}
