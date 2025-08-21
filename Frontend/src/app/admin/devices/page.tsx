'use client';
import { FiRefreshCw, FiPlus, FiSearch, FiServer, FiWifi, FiWifiOff } from 'react-icons/fi';
import { useState, useEffect } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { useRouter } from 'next/navigation';

type Device = {
  id: string;
  hostname: string;
  ip: string;
  status: 'online' | 'offline';
  lastSeen: string;
  type: 'switch' | 'router' | 'firewall';
};

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

  // Mock data - replace with API call
  const devices: Device[] = [
    { id: '1', hostname: 'core-switch-01', ip: '10.0.1.1', status: 'online', lastSeen: '2 mins ago', type: 'switch' },
    { id: '2', hostname: 'edge-router-01', ip: '10.0.2.1', status: 'online', lastSeen: '5 mins ago', type: 'router' },
    { id: '3', hostname: 'fw-dmz-01', ip: '10.0.3.1', status: 'offline', lastSeen: '1 hour ago', type: 'firewall' },
  ];

  const filteredDevices = devices.filter(device =>
    device.hostname.toLowerCase().includes(searchQuery.toLowerCase()) ||
    device.ip.includes(searchQuery)
  );

  const handleRefresh = () => {
    setIsRefreshing(true);
    // Simulate API refresh
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  const getDeviceIcon = (type: Device['type']) => {
    switch (type) {
      case 'switch': return <FiServer className="text-blue-500" />;
      case 'router': return <FiWifi className="text-green-500" />;
      case 'firewall': return <FiServer className="text-red-500" />;
      default: return <FiServer />;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Network Devices</h1>
          <p className="text-gray-500">Manage and monitor all connected network infrastructure</p>
        </div>
        
        <div className="flex gap-2 w-full sm:w-auto">
          <button 
            onClick={handleRefresh}
            disabled={isRefreshing}
            className="flex items-center gap-2 px-4 py-2 bg-white border rounded-lg hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            <FiRefreshCw className={`h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            <span>Refresh</span>
          </button>
          
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <FiPlus className="h-4 w-4" />
            <span>Add Device</span>
          </button>
        </div>
      </div>

      <div className="bg-white border rounded-lg shadow-sm overflow-hidden">
        <div className="p-4 border-b flex items-center justify-between bg-gray-50">
          <div className="relative flex-1 max-w-md">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <FiSearch className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search devices by hostname or IP..."
              className="pl-10 pr-4 py-2 w-full border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          
          <div className="ml-4 text-sm text-gray-500">
            Showing {filteredDevices.length} of {devices.length} devices
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Device</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IP Address</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Seen</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredDevices.map((device) => (
                <tr key={device.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-8 w-8 flex items-center justify-center">
                        {getDeviceIcon(device.type)}
                      </div>
                      <div className="ml-4">
                        <div className="font-medium text-gray-900">{device.hostname}</div>
                        <div className="text-sm text-gray-500 capitalize">{device.type}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-mono">{device.ip}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      device.status === 'online' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {device.status === 'online' ? (
                        <FiWifi className="inline mr-1" />
                      ) : (
                        <FiWifiOff className="inline mr-1" />
                      )}
                      {device.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{device.lastSeen}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button className="text-blue-600 hover:text-blue-900 mr-4">Details</button>
                    <button className="text-gray-600 hover:text-gray-900">Configure</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}