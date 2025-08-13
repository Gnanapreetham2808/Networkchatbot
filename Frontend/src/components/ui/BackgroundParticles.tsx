'use client';

import { useCallback } from 'react';
import Particles from 'react-tsparticles';
import { loadFull } from 'tsparticles';

export default function BackgroundParticles() {
  const particlesInit = useCallback(async (engine: unknown) => {
    await loadFull(engine as any);
  }, []);

  return (
    <Particles
      id="tsparticles"
      init={particlesInit}
      options={{
        fullScreen: { enable: true, zIndex: -1 },
        background: {
          color: '#f9fafb', // same as your light background
        },
        fpsLimit: 60,
        particles: {
          number: {
            value: 50,
            density: {
              enable: true,
              area: 900,
            },
          },
          color: {
            value: ['#2563eb', '#60a5fa'], // primary and lighter brand blues
          },
          links: {
            enable: true,
            distance: 130,
            color: '#2563eb',
            opacity: 0.2,
            width: 1,
          },
          move: {
            enable: true,
            speed: 0.6,
            direction: 'none',
            outModes: {
              default: 'out',
            },
          },
          shape: {
            type: 'circle',
          },
          opacity: {
            value: 0.2,
          },
          size: {
            value: { min: 1, max: 3 },
          },
        },
        interactivity: {
          events: {
            onHover: {
              enable: true,
              mode: 'repulse',
            },
            resize: true,
          },
          modes: {
            repulse: {
              distance: 100,
              duration: 0.4,
            },
          },
        },
        detectRetina: true,
      }}
    />
  );
}
