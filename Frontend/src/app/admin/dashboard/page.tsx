"use client";
import { FiActivity, FiServer, FiShield, FiList } from 'react-icons/fi';
import { useAuth } from '@/components/AuthProvider';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

export default function DashboardPage() {
  const { isAdmin, loading, user } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!loading && user && !isAdmin) router.replace('/not-authorized');
    if (!loading && !user) router.replace('/login');
  }, [isAdmin, loading, user, router]);
  if (loading || (user && !isAdmin)) return <div className="p-6">Loading...</div>;
  const stats = [
    { title: "Active Devices", value: "24", icon: <FiServer className="h-6 w-6" />, trend: "up" },
    { title: "Pending Changes", value: "5", icon: <FiList className="h-6 w-6" />, trend: "neutral" },
    { title: "Security Alerts", value: "2", icon: <FiShield className="h-6 w-6" />, trend: "down" },
    { title: "Avg. Response", value: "320ms", icon: <FiActivity className="h-6 w-6" />, trend: "up" },
  ];

  return (
    <div className="p-6 space-y-6 bg-transparent">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Network Overview</h1>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.title} className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 transition-colors">
            <div className="flex items-center justify-between">
              <div className="text-gray-500 dark:text-gray-400">{stat.title}</div>
              <div className={`p-2 rounded-lg ${stat.trend === 'up' ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400' : stat.trend === 'down' ? 'bg-red-100 dark:bg-red-900/30 text-red-600 dark:text-red-400' : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400'}`}>
                {stat.icon}
              </div>
            </div>
            <div className="mt-2 text-3xl font-semibold text-gray-900 dark:text-gray-100">{stat.value}</div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden transition-colors">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="font-medium text-gray-900 dark:text-gray-100">Recent Configuration Changes</h2>
        </div>
        <div className="divide-y divide-gray-200 dark:divide-gray-700">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
              <div>
                <div className="font-medium text-gray-900 dark:text-gray-100">VLAN Configuration</div>
                <div className="text-sm text-gray-500 dark:text-gray-400">Switch-{i+1}.core</div>
              </div>
              <div className="text-sm text-gray-500 dark:text-gray-400">2 hours ago</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}