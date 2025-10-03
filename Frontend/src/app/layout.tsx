// src/app/layout.tsx
import './globals.css';
import { ReactNode } from 'react';
import { AuthProvider } from '@/components/AuthProvider';
import FirebaseConfigStatus from '@/components/FirebaseConfigStatus';
import NavBar from '@/components/NavBar';

export const metadata = {
  title: 'Network Chatbot',
  description: 'Manage network chatbot users and devices',
};


export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: `
          (function() {
            try {
              const ls = localStorage.getItem('theme');
              const m = window.matchMedia('(prefers-color-scheme: dark)').matches;
              const theme = ls || (m ? 'dark' : 'light');
              if (theme === 'dark') document.documentElement.classList.add('dark');
            } catch(e) {}
          })();
        `}} />
      </head>
      <body className="min-h-screen flex flex-col font-sans bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100 antialiased selection:bg-gray-900 selection:text-white">
        <AuthProvider>
          <NavBar />
          <main className="flex-1 overflow-y-auto">
            <FirebaseConfigStatus />
            {children}
          </main>
        </AuthProvider>
      </body>
    </html>
  );
}
