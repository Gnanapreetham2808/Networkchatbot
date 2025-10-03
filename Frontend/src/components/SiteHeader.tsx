"use client";
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/components/AuthProvider';
import { FiMoon, FiSun, FiLogOut, FiMenu, FiX } from 'react-icons/fi';
import { useState, useEffect } from 'react';
import { track } from '@/lib/analytics';

interface NavItem { href: string; label: string; admin?: boolean; }
const NAV_ITEMS: NavItem[] = [
  { href: '/', label: 'Home' },
  { href: '/chat', label: 'Chat' },
  { href: '/admin/logs', label: 'Logs', admin: true },
  { href: '/admin/dashboard', label: 'Dashboard', admin: true },
  { href: '/admin/devices', label: 'Devices', admin: true },
  { href: '/admin/users', label: 'Users', admin: true },
  { href: '/admin/settings', label: 'Settings', admin: true }
];

export function SiteHeader() {
  const pathname = usePathname();
  const { isAdmin, user, signOutUser } = useAuth();
  const [mounted, setMounted] = useState(false);
  const [theme, setTheme] = useState<'light' | 'dark'>(() => (typeof window !== 'undefined' && document.documentElement.classList.contains('dark') ? 'dark' : 'light'));
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => setMounted(true), []);

  function toggleTheme() {
    const next = theme === 'light' ? 'dark' : 'light';
    setTheme(next);
    if (next === 'dark') document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
    localStorage.setItem('theme', next);
    track('theme_toggle', { to: next });
  }

  function handleNavClick() { setMobileOpen(false); }

  return (
    <header className="sticky top-0 z-50 w-full backdrop-blur-md bg-white/70 dark:bg-gray-900/60 border-b border-gray-200/70 dark:border-gray-800/70">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="h-14 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button aria-label="Menu" className="md:hidden w-9 h-9 inline-flex items-center justify-center rounded-md border border-gray-300 dark:border-gray-700 bg-white/70 dark:bg-gray-800/60" onClick={()=>setMobileOpen(o=>!o)}>
              {mobileOpen ? <FiX className="h-5 w-5"/> : <FiMenu className="h-5 w-5"/>}
            </button>
            <Link href="/" className="font-semibold tracking-tight text-gray-900 dark:text-gray-100 text-lg">NetOps</Link>
            <nav className="hidden md:flex items-center gap-1 text-sm">
              {NAV_ITEMS.filter(i => !i.admin || isAdmin).map(item => {
                const active = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={()=>track('nav_click',{ href:item.href })}
                    className={[
                      'relative px-3 py-2 rounded-md font-medium transition-colors',
                      'text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-200',
                      active && 'text-gray-900 dark:text-white'
                    ].filter(Boolean).join(' ')}
                  >
                    {item.label}
                    {active && <span className="absolute inset-x-2 -bottom-[2px] h-0.5 rounded-full bg-gray-900 dark:bg-gray-200" />}
                  </Link>
                );
              })}
            </nav>
          </div>
          <div className="flex items-center gap-3">
            {mounted && (
              <button onClick={toggleTheme} aria-label="Toggle Theme" className="w-9 h-9 inline-flex items-center justify-center rounded-lg border border-gray-300 dark:border-gray-700 bg-white/70 dark:bg-gray-800/70 hover:bg-gray-100 dark:hover:bg-gray-700 transition">
                {theme === 'light' ? <FiMoon className="h-4 w-4" /> : <FiSun className="h-4 w-4" />}
              </button>
            )}
            {user ? (
              <div className="flex items-center gap-3">
                <div className="hidden sm:flex flex-col leading-tight max-w-[160px]">
                  <span className="text-xs text-gray-500 dark:text-gray-400">Signed in</span>
                  <span className="text-sm font-medium text-gray-800 dark:text-gray-200 truncate">{user.email}</span>
                </div>
                <button onClick={() => { signOutUser(); track('logout'); }} className="flex items-center gap-1 px-3 h-9 rounded-md text-sm font-medium bg-gray-900 text-white hover:bg-gray-800 dark:bg-gray-700 dark:hover:bg-gray-600 transition">
                  <FiLogOut className="h-4 w-4" />
                  <span className="hidden sm:inline">Logout</span>
                </button>
              </div>
            ) : (
              <Link href="/login" onClick={()=>track('nav_click',{ href:'/login' })} className="px-4 h-9 inline-flex items-center rounded-md bg-gray-900 text-white text-sm font-medium hover:bg-gray-800 dark:bg-gray-700 dark:hover:bg-gray-600">Login</Link>
            )}
          </div>
        </div>
      </div>
      {/* Mobile drawer */}
      <div className={`md:hidden fixed inset-x-0 top-14 origin-top transition-transform duration-300 ${mobileOpen ? 'scale-y-100 opacity-100' : 'scale-y-0 opacity-0 pointer-events-none'} bg-white/95 dark:bg-gray-900/95 backdrop-blur-lg border-b border-gray-200 dark:border-gray-800 shadow-lg`}>        
        <nav className="flex flex-col p-4 gap-1 text-sm">
          {NAV_ITEMS.filter(i=>!i.admin||isAdmin).map(item => {
            const active = pathname === item.href || (item.href !== '/' && pathname.startsWith(item.href));
            return (
              <Link key={item.href} href={item.href} onClick={()=>{ handleNavClick(); track('nav_click',{ href:item.href, mobile:true }); }} className={`px-3 py-2 rounded-md font-medium ${active ? 'bg-gray-900 text-white dark:bg-gray-700' : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}`}>{item.label}</Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}