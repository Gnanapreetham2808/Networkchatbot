'use client';

import Link from 'next/link';
import { FiTerminal, FiWifi, FiServer, FiShield, FiArrowRight } from 'react-icons/fi';
import { motion, Variants } from 'framer-motion';

// Best Practice: Define a type for your features for type safety and clarity.
type Feature = {
  icon: JSX.Element;
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

export default function HomePage() {
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
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100 overflow-hidden">
      {/* --- Dynamic Background --- */}
      <div className="absolute top-0 left-0 w-full h-full -z-10">
        <div className="absolute inset-0 bg-grid-gray-200/50 dark:bg-grid-gray-700/30 [mask-image:linear-gradient(to_bottom,white_10%,transparent_100%)]"></div>
        <div className="absolute inset-0 bg-gradient-to-b from-white dark:from-gray-900 to-transparent"></div>
      </div>

      {/* --- Hero Section --- */}
      <section className="py-20 md:py-28 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: 'easeInOut' }}
        >
          <h1 className="text-4xl md:text-6xl font-extrabold text-gray-900 dark:text-white tracking-tight mb-4">
            Network Command Hub
          </h1>
          <p className="text-lg md:text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto mb-10">
            Secure, intelligent automation for your entire network infrastructure.
          </p>
          <div className="mt-10 flex justify-center items-center gap-4 flex-wrap">
            <Link href="/login">
              <button className="px-8 py-3 bg-indigo-600 text-white rounded-lg font-semibold text-base hover:bg-indigo-700 shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 transition-all duration-300 transform hover:scale-105">
                Get Started
              </button>
            </Link>
            <Link href="/chat">
              <button className="px-8 py-3 bg-white dark:bg-gray-800 text-gray-800 dark:text-white border border-gray-300 dark:border-gray-700 rounded-lg font-semibold text-base hover:bg-gray-100 dark:hover:bg-gray-700 hover:border-gray-400 dark:hover:border-gray-600 shadow-sm hover:shadow-md transition-all duration-300 transform hover:scale-105">
                Go to Chat
              </button>
            </Link>
          </div>
        </motion.div>
      </section>

      {/* --- Features Grid --- */}
      <section className="py-16 sm:py-20 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white">A Unified Platform</h2>
          <p className="text-lg text-gray-500 dark:text-gray-400 mt-3">All the tools you need for modern network management.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <FeatureCard key={feature.title} feature={feature} index={index} />
          ))}
        </div>
      </section>

      {/* --- CTA Section --- */}
      <section className="py-20 my-16">
        <div className="max-w-4xl mx-auto text-center px-4">
          <div className="relative p-10 bg-gray-900/70 dark:bg-gray-900/80 backdrop-blur-lg rounded-2xl border border-gray-700 shadow-2xl">
            <h2 className="text-3xl font-bold text-white mb-4">
              Ready to Transform Your Operations?
            </h2>
            <p className="text-lg text-gray-300 mb-8 max-w-2xl mx-auto">
              Join hundreds of engineers automating their infrastructure and reclaiming valuable time.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Link href="/login">
                <button className="px-8 py-3 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium transition-colors duration-300 w-full sm:w-auto">
                  Start a Free Trial
                </button>
              </Link>
              <button className="px-8 py-3 bg-transparent border border-gray-600 text-white hover:bg-gray-800 hover:border-gray-500 rounded-lg font-medium transition-colors duration-300 w-full sm:w-auto">
                Contact Sales
              </button>
            </div>
          </div>
        </div>
      </section>
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