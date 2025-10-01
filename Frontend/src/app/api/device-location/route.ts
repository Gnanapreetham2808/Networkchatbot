import type { NextRequest } from 'next/server';

// Backend base and path(s) are configurable via env; we attempt multiple fallbacks to be resilient.
// NEXT_PUBLIC_BACKEND_BASE: protocol+host+port (no trailing slash)
// NEXT_PUBLIC_BACKEND_DEVICE_LOCATIONS_PATH: optional override path beginning with '/'
const BACKEND_BASE = process.env.NEXT_PUBLIC_BACKEND_BASE?.replace(/\/$/, '') || 'http://localhost:8000';
const OVERRIDE_PATH = process.env.NEXT_PUBLIC_BACKEND_DEVICE_LOCATIONS_PATH;

// Ordered list of candidate relative paths (no query) to try until one succeeds.
// 1. Explicit override
// 2. Plain root include pattern ("" includes chatbot.urls) -> /device-locations/
// 3. Namespaced include pattern -> /api/nlp/device-locations/
// 4. Previous incorrect guess (legacy) -> /api/device-locations/
const CANDIDATE_PATHS = [
  ...(OVERRIDE_PATH ? [OVERRIDE_PATH] : []),
  '/device-locations/',
  '/api/nlp/device-locations/',
  '/api/device-locations/'
];

type BackendAttempt = {
  url: string;
  ok: boolean;
  status?: number;
  error?: string;
};

export async function GET(req: NextRequest) {
  const started = Date.now();
  const { searchParams } = new URL(req.url);
  const sites = (searchParams.get('sites') || 'uk,in').trim() || 'uk,in';

  const attempts: BackendAttempt[] = [];
  let lastData: any = null;

  for (const relPath of CANDIDATE_PATHS) {
    const cleanRel = relPath.startsWith('/') ? relPath : `/${relPath}`;
    const tryUrl = `${BACKEND_BASE}${cleanRel}?sites=${encodeURIComponent(sites)}`;
    try {
      const r = await fetch(tryUrl, { cache: 'no-store' });
      if (!r.ok) {
        attempts.push({ url: tryUrl, ok: false, status: r.status });
        // If 404, keep trying other candidates; for other 5xx still try next.
        continue;
      }
      // Success
      lastData = await r.json();
      attempts.push({ url: tryUrl, ok: true, status: r.status });
      const elapsed = Date.now() - started;
      return new Response(JSON.stringify({ ...lastData, meta: { attempts, elapsed_ms: elapsed } }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (err: any) {
      attempts.push({ url: tryUrl, ok: false, error: err?.message });
      // Try next path
      continue;
    }
  }

  const elapsed = Date.now() - started;
  // Distinguish between upstream not reachable vs all returned non-OK
  const anyNetworkError = attempts.some(a => !!a.error);
  const status = anyNetworkError ? 500 : 502; // 500 if network failure, 502 if backend responded but not OK.
  const body = {
    error: anyNetworkError ? 'fetch_failed' : 'backend_error',
    message: anyNetworkError ? 'Unable to reach backend' : 'Backend responded with non-OK status codes',
    attempts,
    elapsed_ms: elapsed,
    sites
  };
  // Server-side log for debugging (will not leak secrets as we only log URLs and statuses)
  console.error('[device-location] failure', body);
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } });
}
