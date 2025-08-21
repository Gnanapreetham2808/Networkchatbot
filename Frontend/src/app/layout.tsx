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
    <html lang="en">
      <body className="h-screen flex flex-col font-sans bg-gray-50">
        <AuthProvider>
          <NavBar />
          <main className="flex-1 overflow-y-auto p-6">
            <FirebaseConfigStatus />
            {children}
          </main>
        </AuthProvider>
      </body>
    </html>
  );
}
