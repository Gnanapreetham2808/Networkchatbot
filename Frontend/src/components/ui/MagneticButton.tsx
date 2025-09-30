"use client";
import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import React, { useRef } from "react";

interface MagneticButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  intensity?: number; // how far the inner content moves
  radius?: number; // hover radius in px
  children: React.ReactNode;
}

export const MagneticButton: React.FC<MagneticButtonProps> = ({
  intensity = 0.35,
  radius = 120,
  children,
  className = "",
  ...rest
}) => {
  const ref = useRef<HTMLButtonElement | null>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const springX = useSpring(x, { stiffness: 300, damping: 20, mass: 0.3 });
  const springY = useSpring(y, { stiffness: 300, damping: 20, mass: 0.3 });
  const rotateX = useTransform(springY, [ -20, 20 ], [ 8, -8 ]);
  const rotateY = useTransform(springX, [ -20, 20 ], [ -8, 8 ]);

  function handlePointerMove(e: React.PointerEvent) {
    if (!ref.current) return;
    const rect = ref.current.getBoundingClientRect();
    const relX = e.clientX - rect.left - rect.width / 2;
    const relY = e.clientY - rect.top - rect.height / 2;
    const dist = Math.sqrt(relX * relX + relY * relY);
    if (dist < radius) {
      x.set(relX * intensity);
      y.set(relY * intensity);
    }
  }
  function reset() {
    x.set(0); y.set(0);
  }

  return (
    <motion.button
      ref={ref}
      className={`relative overflow-hidden will-change-transform transition-colors ${className}`}
      style={{ perspective: 600 }}
      onPointerMove={handlePointerMove}
      onPointerLeave={reset}
      onBlur={reset}
      {...rest}
    >
      <motion.span
        style={{ x: springX, y: springY, rotateX, rotateY, display: "inline-flex", alignItems: "center", justifyContent: "center", width: "100%", height: "100%" }}
      >
        {children}
      </motion.span>
    </motion.button>
  );
};

export default MagneticButton;
