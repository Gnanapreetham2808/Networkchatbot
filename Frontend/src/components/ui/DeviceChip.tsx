"use client";
import { motion } from "framer-motion";
import React from "react";

interface DeviceChipProps {
  alias?: string;
  host?: string;
  loading?: boolean;
}

const shimmerAnim = {
  initial: { backgroundPosition: "200% 50%" },
  animate: { backgroundPosition: "0% 50%" },
  transition: { duration: 2.5, repeat: Infinity, ease: [0.25, 0.25, 0.75, 0.75] as any }
};

export const DeviceChip: React.FC<DeviceChipProps> = ({ alias, host, loading }) => {
  const content = loading ? "Resolving device..." : alias ? `${alias}${host ? ` (${host})` : ''}` : 'No device';
  const motionProps: any = loading ? shimmerAnim : {};
  return (
    <motion.div
      initial={motionProps.initial}
      animate={motionProps.animate}
      transition={motionProps.transition}
      className="text-xs px-2 py-1 rounded-full font-medium border border-white/30 text-white/90 backdrop-blur-sm bg-gradient-to-r from-white/15 via-white/5 to-white/15 bg-[length:200%_100%]"
      title={host}
    >
      {content}
    </motion.div>
  );
};

export default DeviceChip;
