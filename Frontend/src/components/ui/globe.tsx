"use client";
import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import type { CSSProperties } from 'react';

/*
  Light wrapper around globe.gl for arcs + configurable appearance.
  Usage:
    <World data={arcs} globeConfig={config} />
*/

export interface ArcDatum {
  order?: number;
  startLat: number; startLng: number;
  endLat: number; endLng: number;
  arcAlt?: number;
  color?: string | string[];
  startName?: string;
  endName?: string;
}

export interface GlobeConfig {
  pointSize?: number;
  globeColor?: string;
  showAtmosphere?: boolean;
  atmosphereColor?: string;
  atmosphereAltitude?: number;
  emissive?: string;
  emissiveIntensity?: number;
  shininess?: number;
  polygonColor?: string;
  ambientLight?: string;
  directionalLeftLight?: string;
  directionalTopLight?: string;
  pointLight?: string;
  arcTime?: number;
  arcLength?: number;
  rings?: number;
  maxRings?: number;
  initialPosition?: { lat: number; lng: number };
  autoRotate?: boolean;
  autoRotateSpeed?: number; // degrees per second
  earthImageUrl?: string; // optional custom earth texture
  showArcEndpoints?: boolean; // show points for arc endpoints
  showLabels?: boolean; // show labels for endpoints
  labelFontSize?: number; // base label font size
  debugMarkers?: boolean; // show small debug dots where projection lands
  markerAltitude?: number; // raise markers slightly above surface (in globe radius units)
}

export interface Marker {
  id: string;
  lat: number;
  lng: number;
  render: () => React.ReactNode; // returns the button/element to show
  // optional pixel offset adjustments
  offsetX?: number;
  offsetY?: number;
}

interface WorldProps {
  data: ArcDatum[];
  globeConfig?: GlobeConfig;
  className?: string;
  style?: CSSProperties;
  markers?: Marker[]; // interactive overlay markers
}

export function World({ data, globeConfig = {}, className = '', style, markers = [] }: WorldProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const globeRef = useRef<any>(null);
  const [size, setSize] = useState<{w:number;h:number}>({w:0,h:0});

  // Track container size so we can position markers
  useEffect(() => {
    if (!containerRef.current) return;
    const el = containerRef.current;
    const ro = new ResizeObserver(() => {
      setSize({ w: el.clientWidth, h: el.clientHeight });
    });
    ro.observe(el);
    setSize({ w: el.clientWidth, h: el.clientHeight });
    return () => ro.disconnect();
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (globeRef.current || !containerRef.current) return;
      try {
        const mod: any = await import('globe.gl');
        const createGlobe = mod.default || mod;
        // derive endpoint points for labels if requested
        const endpoints: any[] = [];
        if (globeConfig.showArcEndpoints !== false || globeConfig.showLabels) {
          const seen = new Set<string>();
          for (const arc of data) {
            const entries = [
              { lat: arc.startLat, lng: arc.startLng, label: arc.startName || `${arc.startLat.toFixed(2)}, ${arc.startLng.toFixed(2)}` },
              { lat: arc.endLat, lng: arc.endLng, label: arc.endName || `${arc.endLat.toFixed(2)}, ${arc.endLng.toFixed(2)}` }
            ];
            for (const pt of entries) {
              const key = `${pt.lat.toFixed(3)},${pt.lng.toFixed(3)}`;
              if (!seen.has(key)) {
                seen.add(key);
                endpoints.push(pt);
              }
            }
          }
        }

        const g = createGlobe()(containerRef.current)
          .backgroundColor('rgba(0,0,0,0)')
          .globeImageUrl(globeConfig.earthImageUrl || '//unpkg.com/three-globe/example/img/earth-blue-marble.jpg')
          .showGraticules(false)
          .arcsData(data)
          .arcColor((d: ArcDatum) => d.color || '#2563eb')
          .arcAltitude((d: ArcDatum) => d.arcAlt || 0.25)
          .arcStroke(0.9)
          .arcDashLength(globeConfig.arcLength ?? 0.7)
          .arcDashGap(0.17)
          .arcDashAnimateTime(globeConfig.arcTime ?? 1400)
          .pointsData(globeConfig.showArcEndpoints === false ? [] : endpoints)
          .pointLat((p:any)=>p.lat)
          .pointLng((p:any)=>p.lng)
          .pointAltitude(()=>0.02)
          .pointColor(()=> '#ef4444')
          .pointRadius(()=>0.5)
          .labelsData(globeConfig.showLabels ? endpoints : [])
          .labelLat((p:any)=>p.lat)
          .labelLng((p:any)=>p.lng)
          .labelText((p:any)=>p.label)
          .labelSize(()=> (globeConfig.labelFontSize || 1.2))
          .labelColor(()=> '#111')
          .labelAltitude(()=>0.04);
        // Atmosphere / base colors
        if (globeConfig.showAtmosphere !== false) g.showAtmosphere(true); else g.showAtmosphere(false);
        if (globeConfig.atmosphereColor) g.atmosphereColor(globeConfig.atmosphereColor);
        if (globeConfig.atmosphereAltitude) g.atmosphereAltitude(globeConfig.atmosphereAltitude);

        // Auto-rotate
        if (globeConfig.autoRotate) {
          const speed = globeConfig.autoRotateSpeed ?? 0.5; // degrees per second approx
          let last = performance.now();
          function animate() {
            if (cancelled) return;
            const now = performance.now();
            const dt = (now - last) / 1000;
            last = now;
            const pov = g.pointOfView();
            g.pointOfView({ ...pov, lng: pov.lng + speed * dt });
            requestAnimationFrame(animate);
          }
          requestAnimationFrame(animate);
        }

        // Initial POV
        if (globeConfig.initialPosition) g.pointOfView({ ...globeConfig.initialPosition, altitude: 1.8 });
        else g.pointOfView({ lat: 20, lng: 0, altitude: 2.2 });
        globeRef.current = g;
      } catch (e) {
        console.error('[World] globe init failed', e);
      }
    })();
    return () => { cancelled = true; };
  }, [data, globeConfig]);

  // Project lat/lng to 2D screen coords using globe's internal projection (three.js) once initialized.
  // Maintain animated screen positions for markers so they stay fixed on rotating globe.
  const [markerPositions, setMarkerPositions] = useState<Record<string, { x: number; y: number; visible: boolean }>>({});

  useEffect(() => {
    let af: number;
    function projectLoop() {
      if (globeRef.current && containerRef.current && markers.length) {
        const camera = (globeRef.current as any).camera?.();
        if (camera) {
          const next: Record<string, { x: number; y: number; visible: boolean }> = {};
            // Attempt to read actual globe radius; fallback to 100
            let R = 100;
            try {
              const globeObj = (globeRef.current as any).getGlobe?.();
              const paramR = globeObj?.geometry?.parameters?.radius;
              if (typeof paramR === 'number' && paramR > 0) R = paramR;
            } catch { /* ignore */ }
            const markerAlt = globeConfig.markerAltitude ?? 0; // 0 places on surface
            markers.forEach(m => {
              const { lat, lng } = m;
              // three-globe internal conversion (matching arc/point placement):
              // phi = (90 - lat) * deg2rad, theta = (180 - lng) * deg2rad
              const phi = (90 - lat) * Math.PI / 180;
              const theta = (180 - lng) * Math.PI / 180;
              const rEff = R + markerAlt * R; // allow a fractional raise above surface
              const x = rEff * Math.sin(phi) * Math.cos(theta);
              const y = rEff * Math.cos(phi);
              const z = rEff * Math.sin(phi) * Math.sin(theta);
              const worldPos = new THREE.Vector3(x, y, z);
              // Determine if point faces camera (dot with camera->point vector)
              const cameraDir = new THREE.Vector3().copy(worldPos).sub(camera.position).normalize();
              const normal = worldPos.clone().normalize();
              const facing = normal.dot(cameraDir) > 0;
              const projected = worldPos.clone().project(camera);
              const sx = (projected.x * 0.5 + 0.5) * size.w;
              const sy = (-projected.y * 0.5 + 0.5) * size.h;
              const offscreen = projected.z > 1 || projected.z < -1 || sx < 0 || sy < 0 || sx > size.w || sy > size.h || !facing;
              next[m.id] = { x: sx, y: sy, visible: !offscreen };
            });
          setMarkerPositions(prev => {
            // Avoid excessive renders if unchanged (rough comparison)
            let changed = false;
            for (const k of Object.keys(next)) {
              const a = prev[k]; const b = next[k];
              if (!a || Math.abs(a.x - b.x) > 0.5 || Math.abs(a.y - b.y) > 0.5 || a.visible !== b.visible) { changed = true; break; }
            }
            return changed ? next : prev;
          });
        }
      }
      af = requestAnimationFrame(projectLoop);
    }
    projectLoop();
    return () => cancelAnimationFrame(af);
  }, [markers, size]);

  const markerElements = markers.map(m => {
    const pos = markerPositions[m.id];
    if (!pos || !pos.visible) return null;
    const stylePos: React.CSSProperties = {
      position: 'absolute',
      left: pos.x + (m.offsetX || 0),
      top: pos.y + (m.offsetY || 0),
      transform: 'translate(-50%, -50%)',
      zIndex: 50,
      pointerEvents: 'auto'
    };
    return (
      <div key={m.id} style={stylePos}>
        {globeConfig.debugMarkers && (
          <span className="block w-2 h-2 rounded-full bg-pink-500 absolute -top-1 -left-1 opacity-70" />
        )}
        {m.render()}
      </div>
    );
  });

  return (
    <div ref={containerRef} className={"relative w-full h-full " + className} style={{ minHeight: '500px', ...style }}>
      {markerElements}
    </div>
  );
}

export default World;
