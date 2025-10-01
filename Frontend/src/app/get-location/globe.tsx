"use client";

import React from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { World } from '@/components/ui/globe';
import Effect from './effect';

export default function GetLocationPage() {
  const globeConfig = {
    // Other configs remain the same
    pointSize: 4,
    globeColor: "#1d2238", // Base color (less visible with wireframe)
    showAtmosphere: true,
    atmosphereColor: "#4f46e5",
    atmosphereAltitude: 0.1,
    emissive: "#000000",
    emissiveIntensity: 0.1,
    shininess: 0.9,
    polygonColor: "rgba(255,255,255,0.7)",
    ambientLight: "#ffffff",
    directionalLeftLight: "#ffffff",
    directionalTopLight: "#ffffff",
    pointLight: "#ffffff",
    arcTime: 1000,
    arcLength: 0.9,
    rings: 1,
    maxRings: 3,
    initialPosition: { lat: 28.6139, lng: 77.2090 },
    autoRotate: true,
  autoRotateSpeed: 1.2, // increased from 0.5 for faster rotation
  };

  const sampleArcs = [{ order: 1, startLat: 51.5072, startLng: -0.1276, endLat: 16.5062, endLng: 80.6480, arcAlt: 0.45, color: '#6366f1', startName: 'UK (London)', endName: 'India (Vijayawada)' }];

  const markers = [
    { id: 'london', lat: 51.5072, lng: -0.1276, render: () => (
      <Link href="/chat" className="px-3 py-1 rounded-md bg-indigo-600 hover:bg-indigo-500 text-xs md:text-sm font-medium shadow-lg border border-indigo-300/40 backdrop-blur-sm">LONDON</Link>
    )},
    { id: 'vij', lat: 16.5062, lng: 80.6480, render: () => (
      <Link href="/chat" className="px-3 py-1 rounded-md bg-emerald-600 hover:bg-emerald-500 text-xs md:text-sm font-medium shadow-lg border border-emerald-300/40 backdrop-blur-sm">VIJ</Link>
    )}
  ];

  return (
    <Effect density={900} starColor="#5b86ff">
      <div className="relative flex-1 overflow-hidden">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 1.5 }} className="absolute inset-0 w-full h-full z-0">
          <World data={sampleArcs} globeConfig={globeConfig} markers={markers} />
        </motion.div>
        <motion.div initial={{ opacity: 0, y: -50 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 1, delay: 0.5 }} className="absolute top-6 md:top-10 z-10 w-full text-center px-4">
          <h1 className="text-4xl md:text-6xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-indigo-300 via-sky-300 to-emerald-300 drop-shadow-lg">
            Global Connectivity
          </h1>
          <p className="mt-2 text-sm md:text-lg text-gray-300 font-light">
            Visualizing key geographic locations and connections.
          </p>
        </motion.div>
      </div>
      <div className="w-full border-t border-white/10 bg-gray-900/60 backdrop-blur-sm relative z-10">
        <div className="max-w-5xl mx-auto px-6 py-8">
          <h2 className="text-xl font-semibold tracking-wide mb-4 text-indigo-300">Locations</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="flex items-center justify-between rounded-md bg-gray-800/70 border border-gray-700/60 px-4 py-3">
              <div>
                <p className="text-xs uppercase tracking-wider text-gray-400">Location</p>
                <p className="text-sm md:text-base font-medium">VIJAYAWADA, INDIA</p>
              </div>
              <Link href="/chat" className="text-xs md:text-sm px-3 py-1 rounded-md bg-emerald-600 hover:bg-emerald-500 font-medium shadow">
                VIJAYAWADA
              </Link>
            </div>
            <div className="flex items-center justify-between rounded-md bg-gray-800/70 border border-gray-700/60 px-4 py-3">
              <div>
                <p className="text-xs uppercase tracking-wider text-gray-400">Location</p>
                <p className="text-sm md:text-base font-medium">LONDON, UK</p>
              </div>
              <Link href="/chat" className="text-xs md:text-sm px-3 py-1 rounded-md bg-indigo-600 hover:bg-indigo-500 font-medium shadow">
                LONDON
              </Link>
            </div>
          </div>
        </div>
      </div>
    </Effect>
  );
}