'use client';

import { FiLogOut } from 'react-icons/fi';

export default function LogoutPage() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">
      <div className="bg-white dark:bg-gray-900 shadow-xl rounded-xl p-8 max-w-md w-full text-center">
        <div className="flex justify-center mb-4">
          <FiLogOut className="text-red-500 w-10 h-10" />
        </div>
        <h1 className="text-2xl font-bold text-gray-800 dark:text-white mb-2">You’ve been logged out</h1>
        <p className="text-gray-600 dark:text-gray-300 mb-6">
          Thank you for choosing Stacknets 
        </p>
        <a
          href="/login"
          className="inline-block px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
        >
          Login Again
        </a>
      </div>
    </main>
  );
}
