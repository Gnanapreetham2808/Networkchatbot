'use client';

import { useCallback } from 'react';
import Particles from 'react-tsparticles';
import { loadFull } from 'tsparticles';
import './Waves.css'; // Make sure this file exists and defines .animated-waves

export default function BackgroundEffect() {
  const particlesInit = useCallback(async (engine: unknown) => {
    await loadFull(engine as any); // bypassing type issue with "any"
  }, []);

  return (
    <>
      {/* Animated Waves */}
      <div className="animated-waves fixed inset-0 -z-20" />

      {/* Particle Background */}
      <Particles
        id="tsparticles"
        init={particlesInit}
        options={{
          fullScreen: { enable: true, zIndex: -10 },
          background: { color: 'transparent' },
          fpsLimit: 60,
          particles: {
            number: { value: 80, density: { enable: true, area: 800 } },
            color: { value: '#3b82f6' },
            shape: { type: 'circle' },
            opacity: { value: 0.2 },
            size: { value: { min: 1, max: 4 } },
            move: {
              enable: true,
              speed: 1,
              direction: 'none',
              outModes: { default: 'out' },
            },
            links: {
              enable: true,
              distance: 120,
              color: '#3b82f6',
              opacity: 0.3,
              width: 1,
            },
          },
          detectRetina: true,
        }}
      />
    </>
  );
}
