"use client";

import Link from 'next/link';
import { FiTerminal, FiWifi, FiServer, FiShield, FiArrowRight, FiLock, FiMail, FiChevronRight, FiGlobe } from 'react-icons/fi';
import { motion, Variants } from 'framer-motion';
import React from 'react';
import { Container } from '@/components/ui/primitives/container';
import { Section } from '@/components/ui/primitives/section';
import { Card, CardHeader, CardTitle, CardSubtitle, CardContent } from '@/components/ui/primitives/card';
import { Button } from '@/components/ui/primitives/button';
import { useAuth } from '@/components/AuthProvider';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Squares } from '@/components/ui/squares-background';

// Best Practice: Define a type for your features for type safety and clarity.
type Feature = {
  icon: React.ReactNode;
  title: string;
  description: string;
  link: string | null;
};

// Best Practice: Extract repeatable UI into its own component.
const FeatureCard = ({ feature, index }: { feature: Feature; index: number }) => {
  // A more robust way to handle staggered animations with variants.
  const cardVariants: Variants = {
    offscreen: {
      opacity: 0,
      y: 30,
    },
    onscreen: {
      opacity: 1,
      y: 0,
      transition: {
        type: 'spring',
        bounce: 0.4,
        duration: 0.8,
        delay: index * 0.1,
      },
    },
  };

  const cardContent = (
    <motion.div
      variants={cardVariants}
      initial="offscreen"
      whileInView="onscreen"
      viewport={{ once: true, amount: 0.5 }}
      className="group relative bg-white/80 dark:bg-gray-900/60 backdrop-blur-sm border border-gray-200 dark:border-gray-700 rounded-xl p-6 h-full transition-all duration-300 hover:border-indigo-500/50 hover:shadow-lg hover:-translate-y-1"
    >
      <div className="bg-indigo-100 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-300 rounded-lg w-12 h-12 flex items-center justify-center mb-5">
        {feature.icon}
      </div>
      <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-2">{feature.title}</h3>
      <p className="text-sm text-gray-600 dark:text-gray-400">{feature.description}</p>
      {feature.link && (
        <FiArrowRight className="absolute top-5 right-5 text-gray-400 group-hover:text-indigo-500 transition-colors" />
      )}
    </motion.div>
  );

  return feature.link ? (
    <Link href={feature.link} className="block h-full">
      {cardContent}
    </Link>
  ) : (
    <div className="h-full cursor-default">{cardContent}</div>
  );
};

// Extracted login panel used when no user session present.
function LoginPanel() {
  const { signIn, signUp } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isRegister, setIsRegister] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      // Redirect directly to the globe visualization after auth
      router.push('/globe');
      router.refresh(); // ensure any dependent components re-evaluate auth state
    } catch (err: any) {
      setError(err?.message || 'Authentication failed');
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
        <h1 className="text-2xl font-bold text-center text-gray-800 dark:text-white mb-2">Network Command Hub</h1>
        <p className="text-center text-sm text-gray-500 dark:text-gray-400 mb-6">Sign in to continue</p>
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
          <button type="submit" disabled={pending} className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60 text-white rounded-lg font-semibold transition-colors">
            {pending ? 'Please wait...' : (isRegister ? 'Create Account' : 'Sign In')}
          </button>
        </form>
        <div className="text-center text-sm text-gray-500 dark:text-gray-400 mt-6 space-y-1">
          <p>
            {isRegister ? 'Already have an account?' : 'Don’t have an account?'}{' '}
            <button onClick={()=>setIsRegister(r=>!r)} className="text-indigo-600 hover:underline">{isRegister ? 'Sign In' : 'Register'}</button>
          </p>
        </div>
      </motion.div>
    </main>
  );
}

export default function HomePage() {
  const { user, loading } = useAuth();
  if (loading) return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  if (!user) return <LoginPanel />;
  const features: Feature[] = [
    {
      icon: <FiTerminal className="h-6 w-6" />,
      title: 'CLI Commands',
      description: 'Execute network commands via natural language.',
      link: null,
    },
    {
      icon: <FiWifi className="h-6 w-6" />,
      title: 'Device Management',
      description: 'Monitor and configure network devices.',
      link: '/admin/devices',
    },
    {
      icon: <FiServer className="h-6 w-6" />,
      title: 'Automation',
      description: 'Schedule and automate repetitive tasks.',
      link: null,
    },
    {
      icon: <FiShield className="h-6 w-6" />,
      title: 'Security',
      description: 'Role-based access control for all operations.',
      link: null,
    },
  ];

  return (
    <main className="min-h-screen bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100 overflow-hidden relative">
      {/* Squares background animation */}
      <div className="absolute inset-0 -z-10">
        <Squares 
          direction="diagonal"
          speed={0.3}
          squareSize={80}
          borderColor="rgba(99, 102, 241, 0.6)"
          hoverFillColor="rgba(99, 102, 241, 0.2)"
          className="opacity-80"
        />
      </div>

      {/* Hero */}
      <Section padding="xl" className="relative">
        <Container center className="relative">
          <motion.div initial={{ opacity:0, y:34 }} animate={{ opacity:1, y:0 }} transition={{ duration:.7, ease:[0.25,0.4,0.15,1] }}>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-gray-200 dark:border-gray-800 bg-white/90 dark:bg-gray-900/90 backdrop-blur-md text-xs font-medium text-gray-600 dark:text-gray-400 mb-6 shadow-sm">
              <span className="inline-block w-2 h-2 rounded-full bg-emerald-500 animate-pulse" /> Live NetOps Preview
            </div>
            <h1 className="font-extrabold tracking-tight text-4xl md:text-6xl leading-[1.05] max-w-4xl mx-auto bg-clip-text text-transparent bg-gradient-to-b from-gray-900 to-gray-700 dark:from-white dark:to-gray-300">
              Infinitely Personalized Network Automation
            </h1>
            <p className="mt-6 text-lg md:text-xl text-gray-600 dark:text-gray-400 max-w-2xl mx-auto">
              Execute commands, visualize infrastructure, and monitor device health with AI-assisted workflows.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link href="/chat"><Button size="lg" className="px-8">Open Chat <FiChevronRight className="h-4 w-4" /></Button></Link>
              <Link href="/get-location"><Button size="lg" className="px-8">Globe View <FiChevronRight className="h-4 w-4" /></Button></Link>
            </div>
          </motion.div>

          {/* Removed duplicated tilted feature cards showcase (was above secondary feature grid) */}
        </Container>
      </Section>

    {/* Secondary feature grid (background unified with hero to avoid dual tone) */}
  <Section background="subtle" padding="lg" className="relative bg-white dark:bg-gray-950">
        <Container>
          <div className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-bold tracking-tight">A Unified Platform</h2>
            <p className="mt-3 text-lg text-gray-600 dark:text-gray-400">All the tools you need for modern network management.</p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <FeatureCard key={feature.title} feature={feature} index={index} />
            ))}
          </div>
        </Container>
      </Section>

      {/* Call To Action */}
  <Section padding="xl" className="relative bg-white dark:bg-gray-950">
        <Container center className="max-w-4xl">
          <div className="relative p-10 md:p-14 rounded-2xl border border-gray-200 dark:border-gray-800 bg-gradient-to-br from-gray-50 via-white to-gray-100 dark:from-gray-900 dark:via-gray-900 dark:to-gray-850 text-gray-900 dark:text-white overflow-hidden shadow-2xl transition-colors">
            <div className="pointer-events-none absolute inset-0 opacity-30 mix-blend-overlay bg-[radial-gradient(circle_at_30%_20%,rgba(255,255,255,0.12),transparent_60%)]" />
            <h2 className="text-3xl md:text-4xl font-bold mb-5">Ready to Transform Your Operations?</h2>
            <p className="text-base md:text-lg text-gray-600 dark:text-gray-300 mb-8 max-w-2xl mx-auto">Join engineers automating their infrastructure and reclaiming valuable time with intelligent workflows and unified visibility.</p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/login"><Button size="lg" className="px-8">Start Free Trial <FiChevronRight className="h-4 w-4" /></Button></Link>
              <Button variant="outline" tone="primary" size="lg" className="px-8 text-gray-900 dark:text-white border-gray-300 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-white/10">Contact Sales</Button>
            </div>
          </div>
        </Container>
      </Section>
    </main>
  );
}

// Note: To use the grid background, you may need to add this to your tailwind.config.js
/*
  theme: {
    extend: {
      backgroundImage: {
        'grid-gray-200/50': 'linear-gradient(90deg, rgba(229, 231, 235, 0.5) 1px, transparent 1px), linear-gradient(rgba(229, 231, 235, 0.5) 1px, transparent 1px)',
        'grid-gray-700/30': 'linear-gradient(90deg, rgba(55, 65, 81, 0.3) 1px, transparent 1px), linear-gradient(rgba(55, 65, 81, 0.3) 1px, transparent 1px)',
      },
      backgroundSize: {
        '40': '40px 40px',
      },
    },
  },
*/