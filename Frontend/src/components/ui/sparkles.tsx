"use client";
import React, { useId, useEffect, useState } from "react";
import Particles, { initParticlesEngine } from "@tsparticles/react";
type Container = any;
import { loadSlim } from "@tsparticles/slim";
import { motion, useAnimation } from "framer-motion";
import { cn } from "../../lib/utils";

export type SparklesProps = {
  id?: string;
  className?: string;
  background?: string;
  particleSize?: number; // unused in current options but reserved
  minSize?: number;
  maxSize?: number;
  speed?: number;
  particleColor?: string;
  particleDensity?: number;
};

export const SparklesCore: React.FC<SparklesProps> = (props) => {
  const { id, className, background, minSize, maxSize, speed, particleColor, particleDensity } = props;
  const [init, setInit] = useState(false);

  useEffect(() => {
    initParticlesEngine(async (engine: any) => { await loadSlim(engine); }).then(() => setInit(true));
  }, []);

  const controls = useAnimation();

  const particlesLoaded = async (container?: Container) => {
    if (container) {
      controls.start({ opacity: 1, transition: { duration: 1 } });
    }
  };

  const generatedId = useId();
  return (
    <motion.div animate={controls} className={cn("opacity-0", className)}>
      {init && (
        <Particles
          id={id || generatedId}
          className={cn("h-full w-full")}
          particlesLoaded={particlesLoaded}
          options={{
            background: { color: { value: background || "transparent" } },
            fullScreen: { enable: false, zIndex: 0 },
            fpsLimit: 120,
            interactivity: {
              events: { onClick: { enable: true, mode: "push" }, onHover: { enable: false, mode: "repulse" }, resize: true as any },
              modes: { push: { quantity: 4 }, repulse: { distance: 200, duration: 0.4 } }
            },
            particles: {
              move: {
                enable: true,
                direction: "none",
                speed: { min: 0.1, max: 1 },
                outModes: { default: "out" }
              },
              number: {
                density: { enable: true, width: 400, height: 400 },
                value: particleDensity || 120
              },
              opacity: {
                value: { min: 0.1, max: 1 },
                animation: { enable: true, speed: speed || 4, sync: false, startValue: "random" }
              },
              size: {
                value: { min: minSize || 1, max: maxSize || 3 },
                animation: { enable: false, speed: 5 }
              },
              color: { value: particleColor || "#ffffff" },
              shape: { type: "circle" }
            },
            detectRetina: true
          }}
        />
      )}
    </motion.div>
  );
};
