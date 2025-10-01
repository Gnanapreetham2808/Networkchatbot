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
 * Effect: A simple layout wrapper that injects the star / sparkles background behind its children.
 * Usage:
 *  <Effect><YourContent /></Effect>
 */
export default function Effect({ children, density = 880, starColor = '#5b86ff', pure }: EffectProps) {
  return (
    <div className="relative w-full h-full min-h-screen bg-black text-white overflow-hidden">
      <GalaxyBackground density={density} starColor={starColor} nebula={!pure} vignette={!pure} />
      <div className="relative z-10 w-full h-full">{children}</div>
    </div>
  );
}
