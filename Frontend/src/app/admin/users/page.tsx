'use client';
import { FiUsers, FiPlus, FiEdit2, FiTrash2, FiSearch } from 'react-icons/fi';
import { useState, useEffect } from 'react';
import { useAuth } from '@/components/AuthProvider';
import { useRouter } from 'next/navigation';

type User = {
  id: string;
  name: string;
  email: string;
  role: 'admin' | 'operator' | 'viewer';
  lastActive: string;
};

export default function UsersPage() {
  const { isAdmin, loading, user } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!loading && user && !isAdmin) router.replace('/not-authorized');
    if (!loading && !user) router.replace('/login');
  }, [isAdmin, loading, user, router]);
  if (loading || (user && !isAdmin)) return <div className="p-6">Loading...</div>;
  const [searchQuery, setSearchQuery] = useState('');
  
  // Mock data - replace with API call in future
  const users: User[] = [
    {
      id: '1',
      name: 'Admin User',
      email: 'admin@network.com',
      role: 'admin',
      lastActive: '2 minutes ago'
    },
    {
      id: '2',
      name: 'Network Operator',
      email: 'operator@network.com',
      role: 'operator',
      lastActive: '15 minutes ago'
    },
    {
      id: '3',
      name: 'View Only',
      email: 'viewer@network.com',
      role: 'viewer',
      lastActive: '1 hour ago'
    }
  ];

  const filteredUsers = users.filter(user =>
    user.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    user.email.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <main className="min-h-screen p-6 max-w-6xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <FiUsers className="text-2xl text-blue-600" />
        <h1 className="text-3xl font-bold text-gray-800">User Management</h1>
      </div>

      <div className="bg-white rounded-lg shadow-sm border overflow-hidden">
        {/* Header with search and add button */}
        <div className="p-4 border-b flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div className="relative w-full sm:w-64">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <FiSearch className="text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search users..."
              className="pl-10 pr-4 py-2 w-full border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors whitespace-nowrap">
            <FiPlus />
            Add User
          </button>
        </div>

        {/* Users table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Active</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredUsers.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900">{user.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">{user.email}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      user.role === 'admin' 
                        ? 'bg-purple-100 text-purple-800' 
                        : user.role === 'operator' 
                          ? 'bg-blue-100 text-blue-800' 
                          : 'bg-gray-100 text-gray-800'
                    }`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500">{user.lastActive}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button className="text-blue-600 hover:text-blue-900 mr-4">
                      <FiEdit2 className="inline mr-1" />
                    </button>
                    <button className="text-red-600 hover:text-red-900">
                      <FiTrash2 className="inline" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Empty state */}
        {filteredUsers.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            No users found matching your search
          </div>
        )}

        {/* Future phase notice */}
        <div className="p-4 border-t bg-yellow-50 text-yellow-800 text-sm">
          Note: Full user management functionality is planned for a future release.
        </div>
      </div>
    </main>
  );
}