'use client';

import { useState } from 'react';
import { FiLock, FiMail } from 'react-icons/fi';
import { motion } from 'framer-motion';

export default function LoginPage() {
  const [isAdminMode, setIsAdminMode] = useState(false);

  return (
    <main className="min-h-screen flex items-center justify-center bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="bg-white dark:bg-gray-900 shadow-lg rounded-xl p-8 w-full max-w-md"
      >
        {/* Admin Mode Banner */}
        {isAdminMode && (
          <div className="mb-4 text-sm text-white bg-green-600 px-4 py-2 rounded text-center font-medium">
            You are logging in as <span className="underline">Admin</span>
          </div>
        )}

        <h2 className="text-2xl font-bold text-center text-gray-800 dark:text-white mb-6">
          Login to Your Account
        </h2>

        <form className="space-y-5">
          <div>
            <label className="text-gray-700 dark:text-gray-300 text-sm mb-1 block">Email</label>
            <div className="flex items-center border rounded-lg px-3 py-2 bg-gray-50 dark:bg-gray-800 dark:border-gray-700">
              <FiMail className="text-gray-400 mr-2" />
              <input
                type="email"
                placeholder="you@example.com"
                className="w-full bg-transparent outline-none text-gray-800 dark:text-white"
              />
            </div>
          </div>

          <div>
            <label className="text-gray-700 dark:text-gray-300 text-sm mb-1 block">Password</label>
            <div className="flex items-center border rounded-lg px-3 py-2 bg-gray-50 dark:bg-gray-800 dark:border-gray-700">
              <FiLock className="text-gray-400 mr-2" />
              <input
                type="password"
                placeholder="••••••••"
                className="w-full bg-transparent outline-none text-gray-800 dark:text-white"
              />
            </div>
          </div>

          <button
            type="submit"
            className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-semibold transition-colors"
          >
            Sign In
          </button>
        </form>

        <div className="text-center text-sm text-gray-500 dark:text-gray-400 mt-6 space-y-1">
          <p>
            Don’t have an account?{' '}
            <a href="/register" className="text-blue-600 hover:underline">Register</a>
          </p>
          <p>
            Want to exit the session?{' '}
            <a href="/logout" className="text-red-500 hover:underline">Logout</a>
          </p>
          {!isAdminMode && (
            <p>
              <button
                onClick={() => setIsAdminMode(true)}
                className="text-green-600 hover:underline font-medium"
              >
                Login as Admin
              </button>
            </p>
          )}
        </div>
      </motion.div>
    </main>
  );
}
