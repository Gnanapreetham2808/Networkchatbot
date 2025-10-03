"use client";
import React, { useEffect, useState, useRef } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { motion } from "framer-motion";

const World = dynamic(() => import("@/components/ui/globe").then(m => m.World), { ssr: false });

export default function GetLocationGlobePage() {
  const [locations, setLocations] = useState<{alias:string;site:string;lat:number;lng:number;label:string}[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const r = await fetch('/api/device-location?sites=uk,in', { cache: 'no-store' });
        if (!r.ok) throw new Error(`backend status ${r.status}`);
        const data = await r.json();
        if (!cancelled) {
          setLocations(Array.isArray(data.locations) ? data.locations.filter((l:any)=> l.lat!=null && l.lng!=null) : []);
        }
      } catch (e:any) {
        if (!cancelled) setError(e.message || 'fetch failed');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // Build arc only if we have both sites
  let sampleArcs: any[] = [];
  if (locations.length >= 2) {
    const uk = locations.find(l => l.site === 'uk' || l.label?.toLowerCase().includes('london'));
    const india = locations.find(l => ['in','india','vijayawada'].includes(l.site));
    if (uk && india) {
      sampleArcs = [{
        order:1,
        startLat: uk.lat,
        startLng: uk.lng,
        endLat: india.lat,
        endLng: india.lng,
        arcAlt: 0.45,
        color: '#6366f1',
        startName: uk.label,
        endName: india.label
      }];
    }
  }

  // Track POV altitude from globe
  const globeAltitudeRef = useRef(2.2);
  useEffect(() => {
    const id = window.setInterval(() => {
      // @ts-ignore
      const maybe = (window as any).__WORLD_GLOBE_POV__;
      if (maybe && typeof maybe.altitude === 'number') globeAltitudeRef.current = maybe.altitude;
    }, 1000);
    return () => window.clearInterval(id);
  }, []);

  const markers = locations.map(l => ({
    id: l.alias,
    lat: l.lat,
    lng: l.lng,
    render: () => {
      const short = (l.label || 'SITE').split(' ')[0].toUpperCase();
      const country = l.site.startsWith('uk') ? 'GB' : (['in','india','vijayawada'].includes(l.site) ? 'IN' : short.slice(0,2));
      const baseColor = l.site.startsWith('uk') ? 'indigo' : 'emerald';
      const alt = globeAltitudeRef.current;
      const scale = Math.min(1.25, Math.max(0.75, 2.2 / (alt || 2.2)));
      // Predefined class variants to avoid dynamic tailwind class names being purged
      const colorClasses = baseColor === 'indigo'
        ? 'bg-indigo-600/90 hover:bg-indigo-500 border-indigo-300/50 text-indigo-50'
        : 'bg-emerald-600/90 hover:bg-emerald-500 border-emerald-300/50 text-emerald-50';
      return (
        <Link
          href="/chat"
          aria-label={`Open chat for location ${l.label}`}
          title={l.label}
          className={`group marker-item relative inline-flex items-center gap-1 px-3 py-1 rounded-md text-[10px] md:text-xs font-semibold border backdrop-blur-sm tracking-wide overflow-hidden transition-transform ${colorClasses}`}
          style={{
            textShadow: '0 1px 2px rgba(0,0,0,0.6)',
            transform: `translateZ(0) scale(${scale})`
          }}
          onClick={(e) => {
            const target = e.currentTarget;
            const ripple = document.createElement('span');
            ripple.className = 'absolute inset-0 animate-ping rounded-md bg-white/20 pointer-events-none';
            target.appendChild(ripple);
            setTimeout(()=> ripple.remove(), 500);
          }}
        >
          {/* Halo */}
          <span className="absolute -inset-1 rounded-md bg-gradient-to-br from-white/30 via-white/10 to-transparent opacity-40 blur-md pointer-events-none"></span>
          {/* Inner glowing dot */}
          <span className="relative w-1.5 h-1.5 rounded-full bg-white/90 shadow-inner shadow-black/40" />
          {/* Country initials */}
          <span className="relative font-bold tracking-wider">
            {country}
          </span>
          {/* Short label */}
          <span className="relative hidden sm:inline">{short}</span>
          {/* Tooltip */}
          <span
            className="pointer-events-none opacity-0 group-hover:opacity-100 group-focus:opacity-100 transition-opacity absolute left-1/2 -translate-x-1/2 top-full mt-2 z-50 whitespace-nowrap text-[10px] md:text-xs font-medium px-2.5 py-1.5 rounded-md bg-slate-900/90 backdrop-blur border border-slate-600/40 shadow-lg text-slate-100"
          >
            <span className="block text-[11px] font-semibold mb-0.5 tracking-wide">{l.label}</span>
            <span className="block text-[10px] text-slate-300">Alias: {l.alias}</span>
            <span className="block text-[10px] text-slate-400">{l.lat.toFixed(2)}, {l.lng.toFixed(2)}</span>
          </span>
        </Link>
      );
    }
  }));

  const globeConfig = {
    pointSize: 4,
    globeColor: "#062056",
    showAtmosphere: true,
    atmosphereColor: "#4f46e5",
    atmosphereAltitude: 0.12,
    emissive: "#000000",
    emissiveIntensity: 0.15,
    shininess: 0.9,
    polygonColor: "rgba(255,255,255,0.25)",
    ambientLight: "#ffffff",
    directionalLeftLight: "#ffffff",
    directionalTopLight: "#ffffff",
    pointLight: "#ffffff",
    arcTime: 1400,
    arcLength: 0.85,
    initialPosition: { lat: 35, lng: 30 },
    autoRotate: true,
    autoRotateSpeed: 1.1,
    showLabels: false,
    labelFontSize: 1.6,
    showArcEndpoints: true,
    markerAltitude: 0.01
  } as const;

  return (
    <div className="min-h-screen bg-gradient-to-b from-white via-gray-50 to-gray-100 dark:from-slate-950 dark:via-slate-900 dark:to-black transition-colors text-gray-900 dark:text-white">
      {/* Hero / Globe Section */}
      <section className="relative mx-auto w-full max-w-7xl min-h-[calc(100vh-4rem)] flex flex-col items-center justify-center px-4">
        <motion.div
          initial={{opacity:0,y:-8}}
          animate={{opacity:1,y:0}}
          transition={{duration:0.6}}
          className="text-center max-w-3xl mx-auto z-10 mb-6"
        >
          <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 via-sky-500 to-emerald-600 dark:from-indigo-300 dark:via-sky-300 dark:to-emerald-300">
            Network Locations
          </h1>
          <p className="mt-2 text-sm md:text-base text-gray-600 dark:text-slate-300">
            Current active network endpoints visualized on the globe. Click a location to open the chat.
          </p>
          {loading && <p className="mt-2 text-xs text-gray-500 dark:text-slate-400">Loading locations...</p>}
          {error && !loading && <p className="mt-2 text-xs text-red-500 dark:text-red-400">Failed: {error}</p>}
        </motion.div>

        <div className="relative w-full max-w-[780px] aspect-square">
          <World data={sampleArcs} globeConfig={globeConfig} markers={markers} className="w-full h-full" />
        </div>
      </section>

      {/* Cards Section */}
      <section className="w-full max-w-5xl mx-auto pb-14 px-6 -mt-4">
        <h2 className="sr-only">Locations List</h2>
        <div className="grid gap-5 grid-cols-1 sm:grid-cols-2">
          {locations.map(l => (
            <Link
              key={l.alias}
              href="/chat"
              className={`group border rounded-lg px-5 py-4 transition shadow flex items-center justify-between backdrop-blur-sm ${
                l.site.startsWith('uk')
                  ? 'border-indigo-300 bg-indigo-50 hover:bg-indigo-100 dark:border-indigo-400/30 dark:bg-indigo-900/30 dark:hover:bg-indigo-800/40'
                  : 'border-emerald-300 bg-emerald-50 hover:bg-emerald-100 dark:border-emerald-400/30 dark:bg-emerald-900/30 dark:hover:bg-emerald-800/40'
              }`}
            >
              <div>
                <p className={`text-[11px] uppercase tracking-wider mb-1 ${
                  l.site.startsWith('uk') ? 'text-indigo-600 dark:text-indigo-300/80' : 'text-emerald-600 dark:text-emerald-300/80'
                }`}>
                  Location
                </p>
                <p className="text-sm font-semibold leading-tight text-gray-800 dark:text-gray-100">{l.label}</p>
              </div>
              <span className={`text-[11px] font-medium px-3 py-1 rounded-md text-white ${
                l.site.startsWith('uk')
                  ? 'bg-indigo-600 group-hover:bg-indigo-500'
                  : 'bg-emerald-600 group-hover:bg-emerald-500'
              } transition`}>
                Open Chat
              </span>
            </Link>
          ))}
          {!loading && locations.length === 0 && (
            <div className="col-span-full text-center text-xs text-gray-500 dark:text-slate-400">
              No locations available.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
