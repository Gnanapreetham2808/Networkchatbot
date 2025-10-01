"use client";
import React, { useEffect, useState } from "react";
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

  const markers = locations.map(l => ({
    id: l.alias,
    lat: l.lat,
    lng: l.lng,
    render: () => (
      <Link href="/chat" className={`px-3 py-1 rounded-md text-xs md:text-sm font-medium shadow-lg border backdrop-blur-sm ${l.site.startsWith('uk') ? 'bg-indigo-600 hover:bg-indigo-500 border-indigo-300/40' : 'bg-emerald-600 hover:bg-emerald-500 border-emerald-300/40'}`}>{(l.label||'SITE').split(' ')[0].toUpperCase()}</Link>
    )
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
    initialPosition: { lat: 35, lng: 30 }, // centers roughly between UK & India
    autoRotate: true,
    autoRotateSpeed: 1.1,
    showLabels: true,
    labelFontSize: 1.6,
    showArcEndpoints: true,
    markerAltitude: 0.01
  } as const;

  return (
    <main className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden bg-gradient-to-b from-slate-950 via-slate-900 to-black text-white">
      <motion.div initial={{opacity:0,y:-20}} animate={{opacity:1,y:0}} transition={{duration:1}} className="z-10 mb-6 text-center px-4">
        <h1 className="text-3xl md:text-5xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-300 via-sky-300 to-emerald-300">Network Locations</h1>
        <p className="mt-2 text-sm md:text-base text-slate-300 max-w-xl mx-auto">Current active network endpoints visualized on the globe. Click a location to open the chat.</p>
        {loading && <p className="mt-2 text-xs text-slate-400">Loading locations...</p>}
        {error && !loading && <p className="mt-2 text-xs text-red-400">Failed to load locations: {error}</p>}
      </motion.div>
      <div className="relative w-full max-w-5xl aspect-square md:h-[650px] md:aspect-auto flex items-center justify-center">
        <div className="relative w-full h-full rounded-xl border border-white/10 bg-black/40 backdrop-blur-sm shadow-2xl overflow-hidden">
          <World data={sampleArcs} globeConfig={globeConfig} markers={markers} />
        </div>
      </div>
      <div className="z-10 mt-10 grid gap-4 grid-cols-1 md:grid-cols-2 w-full max-w-3xl px-6">
        {locations.map(l => (
          <Link key={l.alias} href="/chat" className={`group border rounded-lg px-5 py-4 transition shadow flex items-center justify-between ${l.site.startsWith('uk') ? 'border-indigo-400/30 bg-indigo-900/30 hover:bg-indigo-800/40' : 'border-emerald-400/30 bg-emerald-900/30 hover:bg-emerald-800/40'}`}>
            <div>
              <p className={`text-xs uppercase tracking-wider ${l.site.startsWith('uk') ? 'text-indigo-300/80' : 'text-emerald-300/80'}`}>Location</p>
              <p className="text-base font-semibold">{l.label}</p>
            </div>
            <span className={`text-xs font-medium px-3 py-1 rounded-md ${l.site.startsWith('uk') ? 'bg-indigo-600 group-hover:bg-indigo-500' : 'bg-emerald-600 group-hover:bg-emerald-500'} transition`}>Open Chat</span>
          </Link>
        ))}
        {!loading && locations.length === 0 && (
          <div className="col-span-full text-center text-xs text-slate-400">No locations available.</div>
        )}
      </div>
      <div className="pointer-events-none absolute inset-x-0 bottom-0 h-40 bg-gradient-to-t from-black/80 to-transparent" />
    </main>
  );
}
