"use client";
import React, { useMemo } from 'react';
import { SparklesCore } from './sparkles';
import { motion } from 'framer-motion';
import { cn } from '../../lib/utils';

/**
 * GalaxyBackground
 * Layered background: base starfield (SparklesCore), slow parallax stars, and optional nebula gradient.
 */
export interface GalaxyBackgroundProps {
  density?: number;
  starColor?: string;
  className?: string;
  nebula?: boolean;
  vignette?: boolean;
}

export const GalaxyBackground: React.FC<GalaxyBackgroundProps> = ({
  density = 750,
  starColor = '#6ea8ff',
  className,
  nebula = true,
  vignette = true,
}) => {
  // Pre-generate parallax star positions (simple lightweight approach instead of additional lib)
  const parallaxStars = useMemo(() => {
    return Array.from({ length: 90 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      size: Math.random() * 2 + 0.5,
      delay: Math.random() * 6,
      duration: 8 + Math.random() * 10,
      opacity: 0.2 + Math.random() * 0.5,
    }));
  }, []);

  return (
    <div className={cn('absolute inset-0 overflow-hidden', className)}>
      {/* Base particle field */}
      <SparklesCore
        background="transparent"
        minSize={0.3}
        maxSize={1.1}
        particleDensity={density}
        particleColor={starColor}
        speed={2}
        className="w-full h-full"
      />

      {/* Parallax subtle drifting stars */}
      <div className="absolute inset-0 -z-10">
        {parallaxStars.map(s => (
          <motion.span
            key={s.id}
            initial={{ opacity: 0 }}
            animate={{
              opacity: [0, s.opacity, 0],
              scale: [1, 1.2, 1],
              y: [0, -10, 0],
            }}
            transition={{
              repeat: Infinity,
              duration: s.duration,
              delay: s.delay,
              ease: 'easeInOut'
            }}
            style={{
              left: s.x + '%',
              top: s.y + '%',
              width: s.size,
              height: s.size,
              background: starColor,
              filter: 'blur(0.5px)',
            }}
            className="absolute rounded-full shadow-[0_0_4px_rgba(255,255,255,0.4)]"
          />
        ))}
      </div>

      {nebula && (
        <div className="pointer-events-none absolute inset-0 -z-20 mix-blend-screen">
          <div className="absolute inset-0 opacity-40 bg-[radial-gradient(circle_at_30%_40%,rgba(100,60,200,0.35),transparent_60%)]" />
          <div className="absolute inset-0 opacity-30 bg-[radial-gradient(circle_at_70%_60%,rgba(0,150,255,0.30),transparent_65%)]" />
          <div className="absolute inset-0 opacity-20 bg-[radial-gradient(circle_at_50%_50%,rgba(0,180,120,0.25),transparent_70%)]" />
        </div>
      )}

      {vignette && (
        <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_center,rgba(0,0,0,0)_40%,rgba(0,0,0,0.65))]" />
      )}
    </div>
  );
};
