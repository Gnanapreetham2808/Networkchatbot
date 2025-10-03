'use client';
import { FiRefreshCw, FiPlus, FiSearch, FiServer, FiWifi, FiWifiOff, FiAlertCircle, FiClock } from 'react-icons/fi';
import { useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { useRouter } from 'next/navigation';

interface StatusDevice {
  alias: string;
  name: string;
  host: string | null;
  status: 'up' | 'down' | 'unknown';
  latency_ms?: number | null;
  checked_at?: string | null;
}

const POLL_INTERVAL = 15000; // ms (aligns with backend cache ttl)

function relativeTime(iso?: string | null) {
  if (!iso) return '—';
  try {
    const then = new Date(iso).getTime();
    const now = Date.now();
    const diff = Math.max(0, now - then);
    if (diff < 1000 * 60) return `${Math.floor(diff/1000)}s ago`;
    if (diff < 1000 * 60 * 60) return `${Math.floor(diff/60000)}m ago`;
    const h = Math.floor(diff/3600000);
    if (h < 24) return `${h}h ago`;
    return new Date(iso).toLocaleString();
  } catch { return '—'; }
}

function StatusBadge({ status }: { status: StatusDevice['status'] }) {
  const base = 'px-2 inline-flex items-center gap-1 text-xs font-semibold rounded-full';
  if (status === 'up') return <span className={`${base} bg-emerald-100 text-emerald-700 border border-emerald-300/40`}> <FiWifi className=""/> Up</span>;
  if (status === 'down') return <span className={`${base} bg-rose-100 text-rose-700 border border-rose-300/40`}> <FiWifiOff /> Down</span>;
  return <span className={`${base} bg-slate-200 text-slate-700 border border-slate-300/60`}> <FiAlertCircle /> Unknown</span>;
}

export default function DevicesPage() {
  const { isAdmin, loading, user } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!loading && user && !isAdmin) router.replace('/not-authorized');
    if (!loading && !user) router.replace('/login');
  }, [isAdmin, loading, user, router]);
  if (loading || (user && !isAdmin)) return <div className="p-6">Loading...</div>;

  const [searchQuery, setSearchQuery] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [devices, setDevices] = useState<StatusDevice[]>([]);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<NodeJS.Timeout | null>(null);
  const lastFetchRef = useRef<number>(0);

  const fetchDevices = useCallback(async (manual = false) => {
    if (manual) setIsRefreshing(true);
    setError(null);
    try {
      const res = await fetch('/api/device-status', { cache: 'no-store' });
      const json = await res.json();
      if (!res.ok || json.ok === false) {
        throw new Error(json.error || `Status ${res.status}`);
      }
      setDevices(json.devices || []);
      lastFetchRef.current = Date.now();
    } catch (e: any) {
      setError(e.message || 'Failed to load');
    } finally {
      if (manual) setIsRefreshing(false);
    }
  }, []);

  // initial + polling
  useEffect(() => {
    fetchDevices();
    pollRef.current = setInterval(() => fetchDevices(), POLL_INTERVAL);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [fetchDevices]);

  const filtered = devices.filter(d => {
    const q = searchQuery.toLowerCase();
    return d.alias.toLowerCase().includes(q) || (d.name||'').toLowerCase().includes(q) || (d.host||'').includes(q);
  });

  const getIcon = (d: StatusDevice) => {
    // naive type inference from alias prefix
    if (d.alias.startsWith('UK') || d.alias.startsWith('IN')) return <FiServer className="text-indigo-500" />;
    return <FiServer className="text-slate-500" />;
  };

  const lastUpdatedText = lastFetchRef.current ? relativeTime(new Date(lastFetchRef.current).toISOString()) : '—';

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Network Devices</h1>
          <p className="text-gray-500 dark:text-gray-400">Reachability & latency (auto refresh every {POLL_INTERVAL/1000}s)</p>
          <p className="mt-1 text-xs text-gray-400 dark:text-gray-500 flex items-center gap-1"><FiClock className="h-3 w-3"/> Updated {lastUpdatedText}</p>
          {error && <p className="mt-1 text-xs text-rose-600 dark:text-rose-500">Error: {error}</p>}
        </div>
        <div className="flex gap-2 w-full sm:w-auto">
          <button onClick={() => fetchDevices(true)} disabled={isRefreshing} className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50">
            <FiRefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-500 transition-colors">
            <FiPlus className="h-4 w-4" />
            <span>Add Device</span>
          </button>
        </div>
      </div>
  <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm overflow-hidden">
  <div className="p-4 border-b flex items-center justify-between bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700">
          <div className="relative flex-1 max-w-md">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <FiSearch className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search by alias, name or IP..."
              className="pl-10 pr-4 py-2 w-full border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
            />
          </div>
          <div className="ml-4 text-sm text-gray-500 dark:text-gray-400">Showing {filtered.length} of {devices.length} devices</div>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Device</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IP / Host</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Latency</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Checked</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              {filtered.map(d => (
                <tr key={d.alias} className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-8 w-8 flex items-center justify-center">
                        {getIcon(d)}
                      </div>
                      <div className="ml-4">
                        <div className="font-medium text-gray-900 dark:text-gray-100">{d.name || d.alias}</div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 font-mono">{d.alias}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100 font-mono">{d.host || '—'}</td>
                  <td className="px-6 py-4 whitespace-nowrap"><StatusBadge status={d.status} /></td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 dark:text-gray-300">{d.status==='up' && d.latency_ms != null ? `${d.latency_ms} ms` : '—'}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{relativeTime(d.checked_at)}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button
                      onClick={() => fetchDevices(true)}
                      className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300 mr-4 disabled:opacity-40"
                      disabled={isRefreshing}
                    >Recheck</button>
                    <button className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200">Details</button>
                  </td>
                </tr>
              ))}
              {filtered.length===0 && (
                <tr>
                  <td colSpan={6} className="px-6 py-10 text-center text-sm text-gray-500">No devices match your search.</td>
                </tr>) }
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}