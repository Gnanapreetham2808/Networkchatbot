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
        <h1 className="text-3xl font-bold text-gray-800 dark:text-gray-100">User Management</h1>
      </div>

      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden transition-colors">
        {/* Header with search and add button */}
  <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white dark:bg-gray-900">
          <div className="relative w-full sm:w-64">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <FiSearch className="text-gray-400" />
            </div>
            <input
              type="text"
              placeholder="Search users..."
              className="pl-10 pr-4 py-2 w-full border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 dark:hover:bg-blue-500 transition-colors whitespace-nowrap">
            <FiPlus />
            Add User
          </button>
        </div>

        {/* Users table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Email</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Role</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Last Active</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              {filteredUsers.map((user) => (
                <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap font-medium text-gray-900 dark:text-gray-100">{user.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500 dark:text-gray-400">{user.email}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      user.role === 'admin' 
                        ? 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300' 
                        : user.role === 'operator' 
                          ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300' 
                          : 'bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-300'
                    }`}>
                      {user.role}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-gray-500 dark:text-gray-400">{user.lastActive}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button className="text-blue-600 dark:text-blue-400 hover:text-blue-900 dark:hover:text-blue-300 mr-4">
                      <FiEdit2 className="inline mr-1" />
                    </button>
                    <button className="text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300">
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
          <div className="p-8 text-center text-gray-500 dark:text-gray-400">
            No users found matching your search
          </div>
        )}

        {/* Future phase notice */}
        <div className="p-4 border-t bg-yellow-50 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 text-sm border-gray-200 dark:border-gray-700">
          Note: Full user management functionality is planned for a future release.
        </div>
      </div>
    </main>
  );
}