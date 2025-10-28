'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/components/AuthProvider';
import { motion } from 'framer-motion';
import { FiCheck, FiX, FiClock, FiPlay, FiRefreshCw } from 'react-icons/fi';
import MagneticButton from '@/components/ui/MagneticButton';

type VLANIntent = {
  id: number;
  vlan_id: number;
  name: string;
  scope: string;
  status: string;
  created_at: string;
  updated_at: string;
};

type ValidationResult = {
  vlan_id: number;
  results: Record<string, string>;
  summary: string;
  consistent: boolean;
};

export default function VLANManagerPage() {
  const router = useRouter();
  const { user, loading, idToken } = useAuth();
  const [intents, setIntents] = useState<VLANIntent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [applyLoading, setApplyLoading] = useState(false);
  const [selectedIntent, setSelectedIntent] = useState<number | null>(null);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);
  
  const BACKEND_BASE = process.env.NEXT_PUBLIC_BACKEND_URL?.replace('/api/nlp/network-command/', '') || 'http://127.0.0.1:8000';
  const API_URL = `${BACKEND_BASE}/api/vlan-intents/`;

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [loading, user, router]);

  useEffect(() => {
    if (user) {
      fetchIntents();
    }
  }, [user]);

  const fetchIntents = async () => {
    setIsLoading(true);
    try {
      const headers: Record<string, string> = {};
      if (idToken) headers['Authorization'] = `Bearer ${idToken}`;
      const res = await fetch(API_URL, { headers });
      if (res.ok) {
        const data = await res.json();
        setIntents(data);
      }
    } catch (error) {
      console.error('Failed to fetch intents:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const applyPending = async () => {
    setApplyLoading(true);
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (idToken) headers['Authorization'] = `Bearer ${idToken}`;
      const res = await fetch(`${API_URL}apply-intents/`, {
        method: 'POST',
        headers
      });
      if (res.ok) {
        const result = await res.json();
        alert(`✅ Applied: ${result.applied.length}\n⏭️ Skipped: ${result.skipped.length}\n❌ Failed: ${Object.keys(result.failed).length}`);
        fetchIntents();
      } else {
        alert('Failed to apply VLANs');
      }
    } catch (error) {
      console.error('Apply failed:', error);
      alert('Apply request failed');
    } finally {
      setApplyLoading(false);
    }
  };

  const validateIntent = async (id: number, vlanId: number) => {
    setSelectedIntent(id);
    setValidationResult(null);
    try {
      const headers: Record<string, string> = {};
      if (idToken) headers['Authorization'] = `Bearer ${idToken}`;
      const res = await fetch(`${API_URL}${id}/validate/`, { headers });
      if (res.ok) {
        const data = await res.json();
        setValidationResult(data);
      } else {
        alert('Validation failed');
      }
    } catch (error) {
      console.error('Validation error:', error);
      alert('Validation request failed');
    } finally {
      setSelectedIntent(null);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toUpperCase()) {
      case 'APPLIED': return <FiCheck className="text-green-500" />;
      case 'FAILED': return <FiX className="text-red-500" />;
      case 'PENDING': return <FiClock className="text-yellow-500" />;
      default: return <FiClock className="text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toUpperCase()) {
      case 'APPLIED': return 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400';
      case 'FAILED': return 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-400';
      case 'PENDING': return 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-700 dark:text-yellow-400';
      default: return 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400';
    }
  };

  if (loading || (!user && !loading)) {
    return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  }

  return (
    <div className="min-h-screen px-4 py-10 bg-[#f5f7fa] dark:bg-gray-950 transition-colors">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-2">VLAN Automation</h1>
          <p className="text-gray-600 dark:text-gray-400">Manage and deploy VLAN intents across your network</p>
        </div>

        {/* Actions */}
        <div className="mb-6 flex gap-4">
          <MagneticButton
            onClick={fetchIntents}
            disabled={isLoading}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-2 disabled:opacity-50"
          >
            <FiRefreshCw className={isLoading ? 'animate-spin' : ''} />
            Refresh
          </MagneticButton>
          <MagneticButton
            onClick={applyPending}
            disabled={applyLoading || intents.filter(i => i.status === 'PENDING').length === 0}
            className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg flex items-center gap-2 disabled:opacity-50"
          >
            <FiPlay />
            Apply Pending ({intents.filter(i => i.status === 'PENDING').length})
          </MagneticButton>
        </div>

        {/* Intents Table */}
        <div className="bg-white dark:bg-gray-900 rounded-2xl shadow-xl overflow-hidden border border-gray-200 dark:border-gray-700">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
                <tr>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">VLAN ID</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">Scope</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">Created</th>
                  <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {intents.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
                      No VLAN intents found. Create one via chat or API.
                    </td>
                  </tr>
                ) : (
                  intents.map((intent) => (
                    <motion.tr
                      key={intent.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                    >
                      <td className="px-6 py-4 text-sm font-medium text-gray-900 dark:text-white">{intent.vlan_id}</td>
                      <td className="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">{intent.name}</td>
                      <td className="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">{intent.scope}</td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(intent.status)}`}>
                          {getStatusIcon(intent.status)}
                          {intent.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                        {new Date(intent.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => validateIntent(intent.id, intent.vlan_id)}
                          disabled={selectedIntent === intent.id}
                          className="text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300 font-medium disabled:opacity-50"
                        >
                          {selectedIntent === intent.id ? 'Validating...' : 'Validate'}
                        </button>
                      </td>
                    </motion.tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Validation Results */}
        {validationResult && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 bg-white dark:bg-gray-900 rounded-2xl shadow-xl p-6 border border-gray-200 dark:border-gray-700"
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white">
                Validation: VLAN {validationResult.vlan_id}
              </h3>
              <span className={`px-4 py-2 rounded-full text-sm font-medium ${
                validationResult.consistent 
                  ? 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400' 
                  : 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-400'
              }`}>
                {validationResult.consistent ? '✅ Consistent' : '⚠️ Inconsistent'}
              </span>
            </div>
            <p className="text-gray-600 dark:text-gray-400 mb-4">{validationResult.summary}</p>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {Object.entries(validationResult.results).map(([device, status]) => (
                <div
                  key={device}
                  className={`p-4 rounded-lg border ${
                    status === 'ok' 
                      ? 'bg-green-50 dark:bg-green-900/10 border-green-200 dark:border-green-800' 
                      : status === 'missing'
                      ? 'bg-yellow-50 dark:bg-yellow-900/10 border-yellow-200 dark:border-yellow-800'
                      : 'bg-red-50 dark:bg-red-900/10 border-red-200 dark:border-red-800'
                  }`}
                >
                  <div className="font-medium text-gray-900 dark:text-white">{device}</div>
                  <div className={`text-sm ${
                    status === 'ok' ? 'text-green-600 dark:text-green-400' : 
                    status === 'missing' ? 'text-yellow-600 dark:text-yellow-400' : 
                    'text-red-600 dark:text-red-400'
                  }`}>
                    {status.toUpperCase()}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
