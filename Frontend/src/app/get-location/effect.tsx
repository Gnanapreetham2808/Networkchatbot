"use client";
import React from 'react';
import { GalaxyBackground } from '@/components/ui/galaxy-background';

interface EffectProps {
  children?: React.ReactNode;
  density?: number;
  starColor?: string;
  pure?: boolean; // if true, no nebula/vignette
}

/**
 * Effect: A layout wrapper that injects the star / sparkles background
 * and centers children in the viewport.
 */
export default function Effect({
  children,
  density = 880,
  starColor = '#5b86ff',
  pure,
}: EffectProps) {
  return (
    <div className="relative w-full h-full min-h-screen bg-black text-white overflow-hidden">
      <GalaxyBackground
        density={density}
        starColor={starColor}
        nebula={!pure}
        vignette={!pure}
      />
      {/* Centering container */}
      <div className="relative z-10 w-full h-full flex items-center justify-center">
        {children}
      </div>
    </div>
  );
}
