import { FiActivity, FiServer, FiShield, FiList } from 'react-icons/fi';

export default function DashboardPage() {
  const stats = [
    { title: "Active Devices", value: "24", icon: <FiServer className="h-6 w-6" />, trend: "up" },
    { title: "Pending Changes", value: "5", icon: <FiList className="h-6 w-6" />, trend: "neutral" },
    { title: "Security Alerts", value: "2", icon: <FiShield className="h-6 w-6" />, trend: "down" },
    { title: "Avg. Response", value: "320ms", icon: <FiActivity className="h-6 w-6" />, trend: "up" },
  ];

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Network Overview</h1>
      
      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.title} className="bg-white rounded-xl shadow-sm border p-6">
            <div className="flex items-center justify-between">
              <div className="text-gray-500">{stat.title}</div>
              <div className={`p-2 rounded-lg ${stat.trend === 'up' ? 'bg-green-100 text-green-600' : stat.trend === 'down' ? 'bg-red-100 text-red-600' : 'bg-gray-100 text-gray-600'}`}>
                {stat.icon}
              </div>
            </div>
            <div className="mt-2 text-3xl font-semibold">{stat.value}</div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <div className="px-6 py-4 border-b">
          <h2 className="font-medium">Recent Configuration Changes</h2>
        </div>
        <div className="divide-y">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors">
              <div>
                <div className="font-medium">VLAN Configuration</div>
                <div className="text-sm text-gray-500">Switch-{i+1}.core</div>
              </div>
              <div className="text-sm text-gray-500">2 hours ago</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}