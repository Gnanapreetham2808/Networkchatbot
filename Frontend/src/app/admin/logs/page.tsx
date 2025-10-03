'use client';
import { 
  FiSearch, 
  FiFilter, 
  FiDownload, 
  FiClock, 
  FiAlertCircle, 
  FiCheckCircle, 
  FiUser,
  FiServer 
} from 'react-icons/fi';
import { useState, useEffect } from 'react';

type LogEntry = {
  id: string;
  timestamp: Date;
  user: string;
  action: string;
  status: 'success' | 'error' | 'warning';
  device?: string;
  ip: string;
};

export default function LogsPage() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: '',
    user: '',
    search: '',
    dateRange: '24h',
  });

  // Mock data - replace with API call
  useEffect(() => {
    const mockLogs: LogEntry[] = [
      {
        id: '1',
        timestamp: new Date(Date.now() - 1000 * 60 * 5),
        user: 'admin@network.com',
        action: 'Configuration updated on core-switch-01',
        status: 'success',
        device: 'core-switch-01',
        ip: '192.168.1.10',
      },
      {
        id: '2',
        timestamp: new Date(Date.now() - 1000 * 60 * 30),
        user: 'tech@network.com',
        action: 'Failed login attempt',
        status: 'error',
        ip: '203.0.113.42',
      },
      {
        id: '3',
        timestamp: new Date(Date.now() - 1000 * 60 * 120),
        user: 'admin@network.com',
        action: 'VLAN configuration modified',
        status: 'success',
        device: 'edge-switch-02',
        ip: '192.168.1.10',
      },
      {
        id: '4',
        timestamp: new Date(Date.now() - 1000 * 60 * 180),
        user: 'monitor@network.com',
        action: 'High CPU usage detected',
        status: 'warning',
        device: 'core-router-01',
        ip: '192.168.1.15',
      },
    ];
    
    setTimeout(() => {
      setLogs(mockLogs);
      setIsLoading(false);
    }, 800);
  }, []);

  const filteredLogs = logs.filter(log => {
    return (
      (filters.status === '' || log.status === filters.status) &&
      (filters.user === '' || log.user.includes(filters.user)) &&
      (filters.search === '' || 
       log.action.toLowerCase().includes(filters.search.toLowerCase()) ||
       (log.device && log.device.toLowerCase().includes(filters.search.toLowerCase())))
    );
  });

  const getStatusIcon = (status: LogEntry['status']) => {
    switch (status) {
      case 'success': return <FiCheckCircle className="text-green-500" />;
      case 'error': return <FiAlertCircle className="text-red-500" />;
      case 'warning': return <FiAlertCircle className="text-yellow-500" />;
      default: return <FiClock className="text-gray-500" />;
    }
  };

  const formatTimestamp = (date: Date) => {
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Audit Logs</h1>
          <p className="text-gray-500 dark:text-gray-400">System events and configuration changes</p>
        </div>
        
        <div className="flex gap-2 w-full sm:w-auto">
          <select
            value={filters.dateRange}
            onChange={(e) => setFilters({...filters, dateRange: e.target.value})}
            className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 text-gray-900 dark:text-gray-100"
          >
            <option value="1h">Last hour</option>
            <option value="24h">Last 24 hours</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
            <option value="all">All time</option>
          </select>
          
          <button className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors text-gray-700 dark:text-gray-200">
            <FiDownload className="h-4 w-4" />
            <span>Export</span>
          </button>
        </div>
      </div>
      <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm overflow-hidden transition-colors">
        <div className="p-4 border-b bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700 flex flex-col md:flex-row gap-4">
          <div className="relative flex-1 max-w-md">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <FiSearch className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search logs..."
              className="pl-10 pr-4 py-2 w-full border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
              value={filters.search}
              onChange={(e) => setFilters({...filters, search: e.target.value})}
            />
          </div>
          
          <div className="flex gap-2">
            <select
              value={filters.status}
              onChange={(e) => setFilters({...filters, status: e.target.value})}
              className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 text-gray-900 dark:text-gray-100"
            >
              <option value="">All Statuses</option>
              <option value="success">Success</option>
              <option value="error">Error</option>
              <option value="warning">Warning</option>
            </select>
            
            <select
              value={filters.user}
              onChange={(e) => setFilters({...filters, user: e.target.value})}
              className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 text-gray-900 dark:text-gray-100"
            >
              <option value="">All Users</option>
              <option value="admin">Admin</option>
              <option value="tech">Technician</option>
              <option value="monitor">Monitor</option>
            </select>
          </div>
        </div>

        {isLoading ? (
          <div className="p-8 flex items-center justify-center">
            <div className="animate-pulse flex space-x-4">
              <div className="flex-1 space-y-4 py-1">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                <div className="space-y-2">
                  <div className="h-4 bg-gray-200 rounded"></div>
                  <div className="h-4 bg-gray-200 rounded w-5/6"></div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {filteredLogs.length > 0 ? (
              filteredLogs.map((log) => (
                <div key={log.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                  <div className="flex items-start gap-4">
                    <div className="mt-1 flex-shrink-0">
                      {getStatusIcon(log.status)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between">
                        <p className="font-medium text-gray-900 dark:text-gray-100 truncate">{log.action}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400 ml-2 whitespace-nowrap">
                          {formatTimestamp(log.timestamp)}
                        </p>
                      </div>
                      <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-500 dark:text-gray-400">
                        <div className="flex items-center">
                          <FiUser className="mr-1.5 h-3.5 w-3.5 flex-shrink-0 text-gray-400" />
                          {log.user}
                        </div>
                        {log.device && (
                          <div className="flex items-center">
                            <FiServer className="mr-1.5 h-3.5 w-3.5 flex-shrink-0 text-gray-400" />
                            {log.device}
                          </div>
                        )}
                        <div className="font-mono">{log.ip}</div>
                      </div>
                    </div>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center text-gray-500 dark:text-gray-400">
                No logs found matching your filters
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}