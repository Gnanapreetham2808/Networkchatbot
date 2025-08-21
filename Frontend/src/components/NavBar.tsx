"use client";
import Link from 'next/link';
import { useAuth } from '@/components/AuthProvider';

export default function NavBar() {
  const { isAdmin } = useAuth();
  return (
    <header className="bg-black text-white p-4 flex items-center justify-between shadow">
      <h2 className="text-xl font-bold">Network Portal</h2>
      <nav className="flex gap-6 text-sm">
        <Link href="/" className="hover:text-blue-400 transition-colors">Home</Link>
        <Link href="/chat" className="hover:text-blue-400 transition-colors">Chat</Link>
        <Link href="/admin/logs" className="hover:text-blue-400 transition-colors">Logs</Link>
        {isAdmin && <Link href="/admin/dashboard" className="hover:text-blue-400 transition-colors">Dashboard</Link>}
        {isAdmin && <Link href="/admin/users" className="hover:text-blue-400 transition-colors">Users</Link>}
        {isAdmin && <Link href="/admin/devices" className="hover:text-blue-400 transition-colors">Devices</Link>}
        {isAdmin && <Link href="/admin/settings" className="hover:text-blue-400 transition-colors">Settings</Link>}
      </nav>
    </header>
  );
}
