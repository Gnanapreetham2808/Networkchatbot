# Gemini API Setup for Aruba Devices

Your network chatbot now uses **Google Gemini API** (free) for Aruba AOS-CX devices instead of OpenAI.

## Why Gemini?

- ✅ **Free tier**: 1500 requests/day
- ✅ **No billing required**
- ✅ **Easy setup**: Get API key in 2 minutes
- ✅ **Reliable**: Google's production AI infrastructure
- ✅ **Fast**: Gemini 1.5 Flash model optimized for speed

## Setup Steps

### 1. Get Gemini API Key (FREE)

1. Go to: **https://makersuite.google.com/app/apikey**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key (starts with `AIza...`)

### 2. Configure Your Environment

Create or edit `Backend/.env` file:

```bash
# Google Gemini API Key (required for Aruba devices)
GEMINI_API_KEY=AIzaSyC...your-actual-key-here

# Aruba LLM Configuration
ARUBA_LLM_PROVIDER=gemini
ARUBA_LLM_MODEL=gemini-1.5-flash
```

### 3. Restart Backend Server

```powershell
cd Backend\netops_backend
python manage.py runserver
```

## How It Works

### Device-Vendor Routing:

| Device | IP | Vendor | NLP Provider |
|--------|------|--------|--------------|
| **INVIJB1C01** | 192.168.10.1 | Cisco | Local T5 Model |
| **UKLONB10C01** | 192.168.30.1 | Cisco | Local T5 Model |
| **INVIJB10A01** | 192.168.10.10 | **Aruba** | **Gemini API** ✨ |

### Query Examples:

```bash
# Aruba switch (uses Gemini API)
"Show interfaces on Aruba switch"
"Show VLANs on HP switch"
"Show running config on aruba"

# Cisco switches (use local T5 model)
"Show interfaces on London switch"
"Show VLANs on Vijayawada"
```

## Troubleshooting

### Error: "GEMINI_API_KEY not set"

**Solution**: Add the API key to your `.env` file:
```bash
GEMINI_API_KEY=AIzaSyC...your-key
```

### Error: "Gemini HTTP 400"

**Possible causes**:
1. Invalid API key → Check key at https://makersuite.google.com/app/apikey
2. API key restrictions → Remove IP restrictions in API settings
3. Model not available → Try `gemini-1.5-flash` instead:
   ```bash
   ARUBA_LLM_MODEL=gemini-1.5-flash
   ```

### Rate Limits

**Free Tier**: 1500 requests per day (Gemini 1.5 Flash)

If you hit rate limits, consider:
1. Upgrading to Gemini Pro (paid)
2. Implementing request caching
3. Using OpenAI as fallback (requires billing)

## Alternative: Keep Using OpenAI

If you prefer OpenAI (requires billing):

```bash
# .env configuration
ARUBA_LLM_PROVIDER=openai
ARUBA_LLM_MODEL=gpt-4o-mini
OPENAI_API_KEY=sk-...your-openai-key
```

## API Key Security

⚠️ **Never commit `.env` file to Git!**

The `.env` file is already in `.gitignore`. Keep your API keys private.

## Supported Models

### Gemini Models:
- `gemini-1.5-flash` (recommended, fast, free tier: 1500 req/day)
- `gemini-1.5-pro` (more capable, slower, free tier: 50 req/day)
- `gemini-2.0-flash-exp` (experimental, latest features)

### OpenAI Models (if using OpenAI):
- `gpt-4o-mini` (recommended, $0.15/1M tokens)
- `gpt-4o` (more capable, $5/1M tokens)

## Testing

Test your Aruba device connection:

1. Start frontend and backend servers
2. Open chat interface
3. Type: **"Show interfaces on Aruba switch"**
4. Check logs for:
   ```
   [INFO] Gemini prediction completed
   predicted_cli=show interface brief
   connection candidates (primary-host-only)=['192.168.10.10']
   ```

## Cost Comparison

| Provider | Free Tier | Paid Tier |
|----------|-----------|-----------|
| **Gemini 1.5 Flash** | ✅ 1500 req/day | $0.35/1M tokens |
| Gemini 1.5 Pro | ✅ 50 req/day | $3.50/1M tokens |
| OpenAI | ❌ None | $0.15/1M tokens |
| Local T5 | ✅ Unlimited | Free (Cisco only) |

---

## Summary

✅ **Aruba devices → Gemini API (free)**  
✅ **Cisco devices → Local T5 Model (free)**  
✅ **No billing required**  
✅ **2-minute setup**

Get your free API key: https://makersuite.google.com/app/apikey
