// src/app/layout.tsx
import './globals.css';
import { ReactNode } from 'react';
import Link from 'next/link';
import { AuthProvider } from '@/components/AuthProvider';
import FirebaseConfigStatus from '@/components/FirebaseConfigStatus';

export const metadata = {
  title: 'Network Chatbot',
  description: 'Manage network chatbot users and devices',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="h-screen flex flex-col font-sans bg-gray-50">
        <AuthProvider>
        {/* Top Navbar */}
        <header className="bg-black text-white p-4 flex items-center justify-between shadow">
          <h2 className="text-xl font-bold">Admin Panel</h2>
          <nav className="flex gap-6 text-sm">
            <Link href="/" className="hover:text-blue-400 transition-colors">Home</Link>
            <Link href="/admin/dashboard" className="hover:text-blue-400 transition-colors">Dashboard</Link>
            <Link href="/admin/users" className="hover:text-blue-400 transition-colors">Users</Link>
            <Link href="/admin/devices" className="hover:text-blue-400 transition-colors">Devices</Link>
          <Link href="/admin/logs" className="hover:text-blue-400 transition-colors">Logs</Link>
            <Link href="/admin/settings" className="hover:text-blue-400 transition-colors">Settings</Link>
          </nav>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6">
          <FirebaseConfigStatus />
          {children}
        </main>
  </AuthProvider>
      </body>
    </html>
  );
}
