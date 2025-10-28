"use client";
import { motion } from "framer-motion";
import React from "react";
import { FiServer } from "react-icons/fi";

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
  const content = loading 
    ? "Resolving device..." 
    : alias 
      ? `${alias}${host ? ` (${host})` : ''}` 
      : 'No device';
  
  const motionProps: any = loading ? shimmerAnim : {};
  
  return (
    <motion.div
      initial={motionProps.initial}
      animate={motionProps.animate}
      transition={motionProps.transition}
      className="flex items-center gap-2 text-xs px-3 py-1.5 rounded-full font-medium border border-blue-300 dark:border-blue-700 text-blue-700 dark:text-blue-300 bg-gradient-to-r from-blue-100 via-blue-50 to-blue-100 dark:from-blue-900/40 dark:via-blue-900/20 dark:to-blue-900/40 bg-[length:200%_100%] shadow-sm"
      title={host ? `Device: ${alias}\nIP/Hostname: ${host}` : alias}
    >
      <FiServer className="w-3.5 h-3.5" />
      <span>{content}</span>
    </motion.div>
  );
};

export default DeviceChip;
