# Network Chatbot

Network Automation Chatbot: Natural Language to CLI for network devices, with device aliasing, telnet-only execution, and a modern Next.js frontend.

## 🚀 Project Overview

This project enables network administrators to interact with devices using natural language queries. The backend uses Django REST Framework and a local T5 model to convert queries to CLI commands, resolves device aliases, and executes commands via telnet. The frontend (Next.js) provides chat and admin dashboards.

## 📋 Current Status

### ✅ Key Features

- **Backend (Django)**
  - Natural Language → CLI command conversion (T5 model, local only)
  - Device aliasing and hostname resolution (JSON inventory)
  - Telnet-only device execution (Netmiko)
  - Error handling and ambiguity detection
  - API endpoint for chat queries

- **Frontend (Next.js)**
  - Chat interface for network queries
  - Admin dashboard: device management, logs, users
  - Modern UI with Tailwind CSS

### 🏗️ Project Structure

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
cd Backend
pip install -r requirements.txt
cd netops_backend
python manage.py runserver
```

### Frontend Setup
```powershell
cd Frontend
npm install
npm run dev
```

## 📦 Dependencies

### Backend
- Django 5.2.4
- Django REST Framework 3.16.0
- Netmiko 4.6.0 (telnet-only)
- Hugging Face Transformers (local T5 model)
- Paramiko, TextFSM, NTC Templates

### Frontend
- Next.js
- Tailwind CSS

### Globe Visualization (New)
After authentication, users are redirected to a `/globe` route that renders a 3D Earth using `globe.gl` and `three`. It currently displays a small hard‑coded sample of world cities (see `Frontend/src/components/WorldGlobe.tsx`). Click a city label to smoothly focus it.

Customization ideas:
- Replace the `SAMPLE_CITIES` array with data fetched from an internal API (e.g., device geographic metadata).
- Add arcs for traffic flows (use `.arcsData()` in `globe.gl`).
- Overlay polygons for regions or POP coverage.
- Add heatmap coloring based on device health metrics.

Globe code files:
- Component: `Frontend/src/components/WorldGlobe.tsx`
- Page: `Frontend/src/app/globe/page.tsx`

If globe isn’t needed in a deployment, you can remove those two files and the dependencies `globe.gl` and `three` from `package.json`.

Auto-forward option:
- Set `NEXT_PUBLIC_GLOBE_AUTO_FORWARD_MS=8000` (example) in `Frontend/.env.local` to automatically redirect users from `/globe` to `/chat` after 8 seconds. Leave unset to disable.

## 🎯 Next Steps

### Current Features
- Natural language to CLI conversion
- Device aliasing and hostname resolution
- Telnet-only device execution
- Chat and admin UI
- Model files are ignored and not pushed to repo

### Roadmap
- [ ] Security: authentication, RBAC
- [ ] Observability: logging, metrics
- [ ] Device config templates
- [ ] Real-time monitoring
- [ ] Automated tests

## 🤝 Contributing

Contributions and suggestions are welcome! Please open issues or pull requests for improvements.

## 📄 License

MIT License (add details as needed)

---

**Status**: 🟡 In Development  
**Last Updated**: October 1, 2025 (added globe visualization)
