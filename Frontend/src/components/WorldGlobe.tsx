"use client";
import React, { useEffect, useRef, useState } from 'react';

interface CityDatum {
  city: string;
  lat: number;
  lng: number;
  population: number;
  country?: string;
}

// Simple fetch of world cities dataset (subset) - for demo we hardcode a tiny sample
const SAMPLE_CITIES: CityDatum[] = [
  { city: 'London', lat: 51.5072, lng: -0.1276, population: 9000000, country: 'UK' },
  { city: 'New York', lat: 40.7128, lng: -74.0060, population: 8400000, country: 'USA' },
  { city: 'Tokyo', lat: 35.6762, lng: 139.6503, population: 13960000, country: 'Japan' },
  { city: 'Sydney', lat: -33.8688, lng: 151.2093, population: 5312000, country: 'Australia' },
  { city: 'Vijayawada', lat: 16.5062, lng: 80.6480, population: 1040000, country: 'India' },
];

export default function WorldGlobe() {
  const globeRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dims, setDims] = useState<{w:number;h:number}>({w:0,h:0});

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (globeRef.current || !containerRef.current) {
        if (!containerRef.current) {
          console.warn('[WorldGlobe] containerRef is null—component may be unmounted or hidden.');
        }
        return;
      }
      try {
        const mod: any = await import('globe.gl');
        if (cancelled) return;
        const createGlobe = mod.default || mod; // globe.gl exports a function
        console.log('[WorldGlobe] Initializing globe. Container size:', containerRef.current!.clientWidth, 'x', containerRef.current!.clientHeight);
        const g = createGlobe()(containerRef.current!)
          .backgroundColor('#000000')
          .pointOfView({ lat: 20, lng: 10, altitude: 2.2 })
          .showAtmosphere(true)
          .atmosphereColor('#3a98ff')
          .atmosphereAltitude(0.18)
          .labelsData(SAMPLE_CITIES)
          .labelLat((d: CityDatum) => d.lat)
          .labelLng((d: CityDatum) => d.lng)
          .labelText((d: CityDatum) => d.city)
          .labelSize((d: CityDatum) => Math.max(0.6, Math.log10(d.population) / 2))
          .labelColor(() => 'rgba(255,255,255,0.85)')
          .labelResolution(2)
          .onLabelClick((d: CityDatum) => {
            g.pointOfView({ lat: d.lat, lng: d.lng, altitude: 1.5 }, 1500);
          });
        globeRef.current = g;
        setReady(true);
        console.log('[WorldGlobe] Globe ready.');
      } catch (e) {
        console.error('[WorldGlobe] Failed to initialize globe:', e);
        setError((e as any)?.message || 'Initialization failed');
      }
    })();
    return () => { cancelled = true; };
  }, []);

  // Track dimensions (ResizeObserver) for debug; ensure container has height.
  useEffect(() => {
    if (!containerRef.current) return;
    const el = containerRef.current;
    const ro = new ResizeObserver(entries => {
      for (const entry of entries) {
        const cr = entry.contentRect;
        setDims({ w: Math.round(cr.width), h: Math.round(cr.height) });
      }
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  return (
    <div className="relative w-full h-full min-h-[600px] bg-black">
      <div ref={containerRef} className="w-full h-full" />
      {!ready && !error && (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-sm text-gray-300 space-y-2">
          <span>Initializing globe...</span>
          <span className="opacity-60">Container: {dims.w} x {dims.h}</span>
          <span className="opacity-40">If this stays, check browser console for errors.</span>
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-red-300 text-xs p-4 text-center bg-black/70">
          <p className="font-semibold mb-2">Globe failed to load</p>
          <p className="mb-2">{error}</p>
          <ol className="list-decimal list-inside space-y-1 text-left">
            <li>Open DevTools Console for stack trace.</li>
            <li>Verify WebGL enabled (Chrome: chrome://gpu).</li>
            <li>Disable extensions blocking canvas/WebGL.</li>
            <li>Try hard refresh (Ctrl+Shift+R).</li>
          </ol>
        </div>
      )}
    </div>
  );
}
