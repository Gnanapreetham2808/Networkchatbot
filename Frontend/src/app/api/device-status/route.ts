import { NextResponse } from 'next/server';

// Ordered backend path candidates similar to device-location logic
const CANDIDATE_PATHS = [
  '/device-status/',
  '/api/nlp/device-status/',
  '/api/device-status/'
];

function getBackendBase() {
  const env = process.env.NEXT_PUBLIC_BACKEND_BASE || process.env.BACKEND_BASE;
  if (env) return env.replace(/\/$/, '');
  return 'http://localhost:8000';
}

export async function GET(request: Request) {
  const { search } = new URL(request.url);
  const base = getBackendBase();
  const attempts: any[] = [];
  const started = Date.now();
  for (const p of CANDIDATE_PATHS) {
    const url = base + p + (search || '');
    const t0 = Date.now();
    try {
      const r = await fetch(url, { cache: 'no-store' });
      const text = await r.text();
      attempts.push({ path: p, status: r.status, ms: Date.now() - t0 });
      if (r.ok) {
        try {
          const data = JSON.parse(text);
          return NextResponse.json({
            ok: true,
            devices: data.devices || data || [],
            count: data.count ?? (Array.isArray(data.devices) ? data.devices.length : undefined),
            backend_base: base,
            attempts,
            elapsed_ms: Date.now() - started
          }, { status: 200 });
        } catch (e) {
          return NextResponse.json({ ok: false, error: 'invalid_json', body: text, attempts, elapsed_ms: Date.now() - started }, { status: 502 });
        }
      }
    } catch (e: any) {
      attempts.push({ path: p, error: e?.message || 'fetch_failed', ms: Date.now() - t0 });
    }
  }
  return NextResponse.json({ ok: false, error: 'all_paths_failed', attempts, elapsed_ms: Date.now() - started }, { status: 502 });
}
