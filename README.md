# Network Chatbot

Natural Language → CLI network automation platform with a Django REST backend, device alias resolution, and a modern Next.js (App Router) frontend. Now includes a resilient globe device‑location API layer with automatic backend path fallbacks.

## 🚀 Project Overview

This project enables network administrators to interact with devices using natural language queries. The backend uses Django REST Framework and a local T5 model to convert queries to CLI commands, resolves device aliases, and executes commands via telnet. The frontend (Next.js) provides chat and admin dashboards.

Recent updates:
- Vendor-aware routing:
  - Aruba/HPE → OpenAI (always)
  - Cisco → local model first; fallback to OpenAI (Cisco prompt) on failure
- Location stripping for OpenAI (uk, london, india, in, vijayawada, hyderabad, hyderabaad, hyd, lab, aruba) so prompts focus on intent
- Globe API now returns Hyderabad; `sites=in` returns both Vijayawada and Hyderabad

## 📋 Current Status

### ✅ Key Features

- **Backend (Django)**
  - Natural Language → CLI command conversion (local T5 variants)
  - Device aliasing & hostname resolution (`Devices/device_resolver.py`)
  - Telnet-only execution (Netmiko) with prompt normalization & noise filtering
  - Device location aggregation endpoint with coordinate fallbacks
  - Authentication stub (`MeAPIView`) and extensible RBAC placeholder
  - Defensive parsing & ambiguity reporting for unsafe/ambiguous commands

- **Frontend (Next.js)**
  - Chat interface for network queries
  - Admin dashboard: device management, logs, users
  - Modern UI with Tailwind CSS

### 🏗️ Project Structure (Simplified)

```
Networkchatbot/
├── Backend/
│   ├── netops_backend/
│   │   ├── chatbot/
│   │   │   ├── views.py
│   │   │   ├── nlp_model.py
│   │   │   ├── network.py
│   │   │   └── nlp_engine/
│   │   ├── Devices/
│   │   │   ├── devices.json
│   │   │   ├── device_resolver.py
│   │   └── ...
│   └── manage.py
├── Frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── chat/
│   │   │   ├── admin/
│   │   └── components/
│   └── ...
└── README.md
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- Git

### Backend Setup
```powershell
git clone <repository-url>
cd Networkchatbot
python -m venv .venv
.venv\Scripts\activate
pip install -r Backend\requirements.txt
cd Backend\netops_backend
..\..\nautobot-venv\Scripts\python.exe manage.py runserver 8000
# or if your venv is active:
# python manage.py runserver 8000
```

### Frontend Setup
```powershell
cd Frontend
npm install
npm run dev
```

## 🌱 Environment Variables

Create `Frontend/.env.local` and (optionally) `Backend/.env` (example names — adapt as needed). Only non‑secret, frontend‑visible vars should be prefixed with `NEXT_PUBLIC_`.

Frontend `.env.local` example:
```
NEXT_PUBLIC_BACKEND_BASE=http://localhost:8000
# Override if backend device locations endpoint is non-standard
# NEXT_PUBLIC_BACKEND_DEVICE_LOCATIONS_PATH=/device-locations/
# Optional auto-forward after globe (ms)
# NEXT_PUBLIC_GLOBE_AUTO_FORWARD_MS=8000
```

Backend (Django) example `.env` (NOT committed):
```
DISABLE_AUTH=1               # For development only
DEVICES_RELOAD_EACH_REQUEST=0

# Aruba → OpenAI (always)
ARUBA_LLM_MODEL=gpt-5o-mini
# Optional Aruba prompt
# ARUBA_SYSTEM_PROMPT=You are a precise network CLI assistant... (AOS-CX)

# Cisco local first; fallback to OpenAI if local fails
CISCO_FALLBACK_PROVIDER=openai
CISCO_FALLBACK_MODEL=gpt-4o-mini
# Optional Cisco prompt
# CISCO_SYSTEM_PROMPT=You are a precise network CLI assistant... (Cisco IOS)

# OpenAI
OPENAI_API_KEY=sk-...
CLI_LLM_TIMEOUT=15
```

## 📦 Dependencies

### Backend
- Django 5.2.4
- Django REST Framework 3.16.0
- Netmiko 4.6.0 (telnet-only)
- Hugging Face Transformers (local T5 model)
- Paramiko, TextFSM, NTC Templates

### Frontend
- Next.js (App Router)
- Tailwind CSS + class variance utilities
- SWR for lightweight data fetching
- Globe visualization: `globe.gl`, `three`

### Globe Visualization & Device Locations
The `/globe` page renders a 3D Earth (Three.js + `globe.gl`). Device markers come from the frontend API route: `GET /api/device-location?sites=uk,in`.

`/api/device-location` server route logic:
1. Reads `sites` query (comma-separated aliases or regions).
2. Tries backend candidates in this order until success:
  - `NEXT_PUBLIC_BACKEND_DEVICE_LOCATIONS_PATH` (if set)
  - `/device-locations/`
  - `/api/nlp/device-locations/`
  - `/api/device-locations/` (legacy fallback)
3. Aggregates attempts & timing in `meta` for diagnostics.
4. Returns:
  ```json
  { "locations": [ { "alias": "UKLONB1SW2", "lat": 51.5072, "lng": -0.1276, "label": "UK - London" } ],
    "meta": { "attempts": [ { "url": "http://localhost:8000/device-locations/?sites=uk,in", "ok": true, "status": 200 } ], "elapsed_ms": 42 } }
  ```
5. On failure, differentiates between network (500) and non-OK backend responses (502) with a detailed `attempts` array.

Hyderabad support:
- `sites=uk,in` returns UK + both India markers (Vijayawada and Hyderabad)
- `sites=uk,hyderabad` forces UK ↔ Hyderabad arc (typo `hyderabaad` also accepted)

Coordinate fallback: If a device record lacks `lat/lng`, predefined site defaults fill in (see `DeviceLocationAPIView.FALLBACK_COORDS`).

Customization ideas:
- Replace site detection heuristics with DB-driven inventory.
- Add arcs for inter-site traffic flows.
- Layer health metrics or SLA heatmaps.

Customization ideas:
- Replace the `SAMPLE_CITIES` array with data fetched from an internal API (e.g., device geographic metadata).
- Add arcs for traffic flows (use `.arcsData()` in `globe.gl`).
- Overlay polygons for regions or POP coverage.
- Add heatmap coloring based on device health metrics.

Globe code files:
- Component: `Frontend/src/components/WorldGlobe.tsx`
- API route: `Frontend/src/app/api/device-location/route.ts`
- Page: `Frontend/src/app/globe/page.tsx`

If globe isn’t needed, remove those files and drop `globe.gl` & `three` from `package.json`.

Auto-forward option:
- Set `NEXT_PUBLIC_GLOBE_AUTO_FORWARD_MS=8000` (example) in `Frontend/.env.local` to automatically redirect users from `/globe` to `/chat` after 8 seconds. Leave unset to disable.

## 🧪 Testing (Manual Quick Checks)

Backend health:
```powershell
curl http://localhost:8000/device-locations/
```

Frontend device location API (after `npm run dev`):
```powershell
curl http://localhost:3000/api/device-location?sites=uk,in
```

Expect 200 with `locations` & `meta`. If 502/500, inspect `meta.attempts` URLs.

## 🛠️ Troubleshooting

| Issue | Likely Cause | Fix |
|-------|--------------|-----|
| 502 from `/api/device-location` | Wrong backend path or backend returned non-OK | Set `NEXT_PUBLIC_BACKEND_BACKEND_DEVICE_LOCATIONS_PATH` or ensure Django path `/device-locations/` works |
| 500 from `/api/device-location` | Backend unreachable / network error | Check server running on `localhost:8000` & firewall |
| Missing `next-server` runtime module | Mixed `"latest"` Next/React versions | Pin stable Next + React in `package.json` |
| Device lat/lng null | Missing coordinates in inventory | Add coordinates or extend fallback map |
| Auth always unauthenticated | `DISABLE_AUTH` not set | Use `DISABLE_AUTH=1` for dev, implement real auth later |

## 🧹 Repository Hygiene

- `nautobot-docker-compose/` removed & now ignored to reduce repo size/clutter.
- Large model artifacts & binary weights are ignored by `.gitignore`.
- Nested accidental Git repos eliminated.

To fully purge a removed directory from history (optional):
```powershell
pip install git-filter-repo
git filter-repo --path nautobot-docker-compose --invert-paths
git push --force origin main
```

## 🎯 Next Steps

### Current Features
- Natural language to CLI conversion
- Device aliasing and hostname resolution
- Telnet-only device execution
- Chat and admin UI
- Model files are ignored and not pushed to repo

### Roadmap
- [ ] Security hardening: auth & RBAC
- [ ] Observability: structured logs + metrics exporter
- [ ] Automated tests (pytest + React component tests)
- [ ] Device config templating & change previews
- [ ] Real-time telemetry (WebSockets / SSE)
- [ ] Multi-vendor device abstraction layer

## 🤝 Contributing

Contributions and suggestions are welcome! Please open issues or pull requests for improvements.

## 📄 License

MIT License (add details as needed)

---

**Status**: 🟡 In Development  
**Last Updated**: October 17, 2025 (Aruba→OpenAI, Cisco fallback, Hyderabad globe)
