"use client";
import { ReactNode, useEffect, useState, useContext, createContext } from 'react';
import { auth } from '@/lib/firebaseClient';
import { onAuthStateChanged, User, getIdToken, signInWithEmailAndPassword, createUserWithEmailAndPassword, signOut } from 'firebase/auth';

type AuthCtx = {
  user: User | null;
  loading: boolean;
  idToken: string | null;
  isAdmin: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOutUser: () => Promise<void>;
};

const Ctx = createContext<AuthCtx>({ user: null, loading: true, idToken: null, isAdmin: false, signIn: async()=>{}, signUp: async()=>{}, signOutUser: async()=>{} });

export const useAuth = () => useContext(Ctx);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [idToken, setIdToken] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  const ADMIN_EMAILS = (process.env.NEXT_PUBLIC_ADMIN_EMAILS || '')
    .split(',')
    .map(e => e.trim().toLowerCase())
    .filter(Boolean);

  useEffect(() => {
    const unsub = onAuthStateChanged(auth, async (u) => {
      setUser(u);
      if (u) {
        try {
          const t = await getIdToken(u, /* forceRefresh */ true);
          setIdToken(t);
        } catch (e) {
          console.error('Token error', e);
          setIdToken(null);
        }
        const emailLower = (u.email || '').toLowerCase();
        setIsAdmin(ADMIN_EMAILS.includes(emailLower));
      } else {
        setIdToken(null);
        setIsAdmin(false);
      }
      setLoading(false);
    });
    return () => unsub();
  }, []);

  async function signIn(email: string, password: string) {
    await signInWithEmailAndPassword(auth, email, password);
  }
  async function signUp(email: string, password: string) {
    await createUserWithEmailAndPassword(auth, email, password);
  }
  async function signOutUser() {
    await signOut(auth);
  }

  return <Ctx.Provider value={{ user, loading, idToken, isAdmin, signIn, signUp, signOutUser }}>{children}</Ctx.Provider>;
}
