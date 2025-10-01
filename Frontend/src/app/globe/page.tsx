"use client";
import React, { useEffect } from 'react';
import WorldGlobe from '@/components/WorldGlobe';
import { useAuth } from '@/components/AuthProvider';
import { useRouter } from 'next/navigation';
import Link from 'next/link';

export default function GlobePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  // Protect route
  useEffect(() => {
    if (!loading && !user) {
      router.replace('/');
    }
  }, [user, loading, router]);

  // Optional auto-forward to chat after viewing globe (configurable)
  useEffect(() => {
    if (!user) return;
    const msRaw = process.env.NEXT_PUBLIC_GLOBE_AUTO_FORWARD_MS;
    if (!msRaw) return; // disabled if not set
    const ms = parseInt(msRaw, 10);
    if (Number.isNaN(ms) || ms <= 0) return;
    const id = setTimeout(() => {
      router.push('/chat');
    }, ms);
    return () => clearTimeout(id);
  }, [user, router]);

  if (loading) return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  if (!user) return null;

  return (
    <main className="min-h-screen flex flex-col">
      <header className="flex items-center justify-between px-6 py-4 bg-gray-900 text-white shadow">
        <h1 className="font-semibold text-lg">Global Network View</h1>
        <nav className="space-x-4 text-sm">
          <Link href="/">Home</Link>
          <Link href="/chat" className="underline underline-offset-4">Chat</Link>
        </nav>
      </header>
      <div className="flex-1 relative bg-black">
        <WorldGlobe />
        <div className="absolute bottom-4 left-4 bg-black/50 text-white text-xs px-3 py-2 rounded-md backdrop-blur-sm border border-white/10 space-y-1">
          <p>Click a city label to focus. Demo dataset subset.</p>
          <p>
            <Link href="/chat" className="inline-block mt-1 px-3 py-1 bg-indigo-600 hover:bg-indigo-700 text-white rounded transition-colors text-xs font-medium">Go to Chat</Link>
          </p>
          {process.env.NEXT_PUBLIC_GLOBE_AUTO_FORWARD_MS && (
            <p className="opacity-70">Auto-forward in {Math.round((parseInt(process.env.NEXT_PUBLIC_GLOBE_AUTO_FORWARD_MS,10)||0)/1000)}s…</p>
          )}
        </div>
      </div>
    </main>
  );
}
