'use client';

import { useState } from 'react';
import { FiLock, FiMail } from 'react-icons/fi';
import { motion } from 'framer-motion';
import { useAuth } from '@/components/AuthProvider';
import { useRouter } from 'next/navigation';

export default function LoginPage() {
  const [isAdminMode, setIsAdminMode] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);
  const { signIn, signUp, user, isAdmin } = useAuth();
  const router = useRouter();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setPending(true);
    try {
      if (isRegister) {
        await signUp(email, password);
      } else {
        await signIn(email, password);
      }
      // Post-login routing based on admin status
      if (isAdminMode || isAdmin) {
        router.push('/admin/dashboard');
      } else {
        router.push('/chat');
      }
    } catch (err: any) {
      const code = err?.code || '';
      let msg = err?.message || 'Authentication failed';
      switch (code) {
        case 'auth/configuration-not-found':
          msg = 'Email/Password provider not enabled in Firebase console (Authentication > Sign-in method). Enable it and retry.';
          break;
        case 'auth/invalid-api-key':
          msg = 'Invalid API key. Re-copy config from Firebase project settings.';
          break;
        case 'auth/network-request-failed':
          msg = 'Network error reaching Firebase. Check connectivity / ad blockers.';
          break;
        case 'auth/email-already-in-use':
          msg = 'Email already registered. Switch to Sign In.';
          break;
        case 'auth/invalid-email':
          msg = 'Invalid email format.';
          break;
        case 'auth/weak-password':
          msg = 'Password too weak (min 6 chars).';
          break;
      }
      setError(msg);
    } finally {
      setPending(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-gradient-to-b from-gray-50 to-white dark:from-gray-900 dark:to-gray-800">
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="bg-white dark:bg-gray-900 shadow-lg rounded-xl p-8 w-full max-w-md"
      >
        {/* Admin Mode Banner */}
    {(isAdminMode || isAdmin) && (
          <div className="mb-4 text-sm text-white bg-green-600 px-4 py-2 rounded text-center font-medium">
      {isAdmin ? 'Authenticated as Admin' : 'You are logging in as Admin'}
          </div>
        )}

        <h2 className="text-2xl font-bold text-center text-gray-800 dark:text-white mb-6">
          Login to Your Account
        </h2>

        <form className="space-y-5" onSubmit={handleSubmit}>
          <div>
            <label className="text-gray-700 dark:text-gray-300 text-sm mb-1 block">Email</label>
            <div className="flex items-center border rounded-lg px-3 py-2 bg-gray-50 dark:bg-gray-800 dark:border-gray-700">
              <FiMail className="text-gray-400 mr-2" />
              <input type="email" value={email} onChange={e=>setEmail(e.target.value)} placeholder="you@example.com" className="w-full bg-transparent outline-none text-gray-800 dark:text-white" required />
            </div>
          </div>

          <div>
            <label className="text-gray-700 dark:text-gray-300 text-sm mb-1 block">Password</label>
            <div className="flex items-center border rounded-lg px-3 py-2 bg-gray-50 dark:bg-gray-800 dark:border-gray-700">
              <FiLock className="text-gray-400 mr-2" />
              <input type="password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="••••••••" className="w-full bg-transparent outline-none text-gray-800 dark:text-white" required />
            </div>
          </div>

          {error && <div className="text-sm text-red-500">{error}</div>}
          <button type="submit" disabled={pending} className="w-full py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white rounded-lg font-semibold transition-colors">
            {pending ? 'Please wait...' : (isRegister ? 'Create Account' : 'Sign In')}
          </button>
        </form>

        <div className="text-center text-sm text-gray-500 dark:text-gray-400 mt-6 space-y-1">
          <p>
            {isRegister ? 'Already have an account?' : 'Don’t have an account?'}{' '}
            <button onClick={()=>setIsRegister(r=>!r)} className="text-blue-600 hover:underline">{isRegister ? 'Sign In' : 'Register'}</button>
          </p>
          <p>
            Want to exit the session?{' '}
            <a href="/logout" className="text-red-500 hover:underline">Logout</a>
          </p>
          {!isAdminMode && !isRegister && (
            <p><button onClick={() => setIsAdminMode(true)} type="button" className="text-green-600 hover:underline font-medium">Login as Admin</button></p>
          )}
        </div>
      </motion.div>
    </main>
  );
}
