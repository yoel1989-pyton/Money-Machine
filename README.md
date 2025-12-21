# 💰 MONEY MACHINE
## The Autonomous Omni-Channel Revenue Engine

![Money Machine](https://img.shields.io/badge/Status-Production%20Ready-green)
![License](https://img.shields.io/badge/License-MIT-blue)
![Budget](https://img.shields.io/badge/Budget-%2450%2Fmo-orange)

A fully autonomous content-to-cash conversion engine that runs 24/7 on Railway, creating and distributing content across all platforms while managing finances and self-healing from errors.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    💰 MONEY MACHINE                              │
│                   Railway + n8n + Python                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  🎯      │  │  🎨      │  │  📡      │  │  💰      │        │
│  │  HUNTER  │─▶│  CREATOR │─▶│ GATHERER │─▶│BUSINESS  │        │
│  │  ENGINE  │  │  ENGINE  │  │  ENGINE  │  │  ENGINE  │        │
│  └────┬─────┘  └──────────┘  └──────────┘  └────┬─────┘        │
│       │                                          │              │
│       └──────────────┐   ┌───────────────────────┘              │
│                      │   │                                       │
│                  ┌───▼───▼───┐                                  │
│                  │   🛡️      │                                  │
│                  │  SURVIVOR │                                  │
│                  │   ENGINE  │                                  │
│                  └───────────┘                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 The 5 Engines

| Engine | Purpose | Key Features |
|--------|---------|--------------|
| 🎯 **Hunter** | Find opportunities | Reddit trends, Google Trends, YouTube gaps, Affiliate opportunities |
| 🎨 **Creator** | Produce content | TTS (Edge, FREE), FFmpeg video assembly, Script generation |
| 📡 **Gatherer** | Distribute everywhere | YouTube, TikTok, Instagram, Pinterest (Official APIs) |
| 💰 **Businessman** | Manage money | Stripe, PayPal, Mercury, reinvestment logic |
| 🛡️ **Survivor** | Stay alive | Error handling, health monitoring, self-healing, alerts |

---

## 💵 Budget Breakdown ($50/month MAX)

| Service | Cost | What You Get |
|---------|------|--------------|
| Railway | $5-20 | n8n hosting, PostgreSQL, Redis |
| OpenAI | $0-10 | Script generation (optional, has free tier) |
| Domain | $0-10 | Optional custom domain |
| Proxy | $0-10 | Optional for advanced features |
| **TOTAL** | **≤$50** | Full autonomous system |

### 🆓 100% FREE Services Used

- **Edge TTS**: Microsoft's free text-to-speech (unlimited)
- **Pexels/Pixabay**: Free stock video (unlimited)
- **YouTube API**: 10,000 units/day free
- **Reddit API**: 60 requests/minute free
- **Stripe**: Free until you make money (2.9% + $0.30 per transaction)
- **Beehiiv**: Free up to 2,500 email subscribers
- **Telegram/Discord**: Free alerts (unlimited)

---

## 🚀 Quick Start (15 minutes)

### Step 1: Fork & Clone

```bash
git clone https://github.com/YOUR_USERNAME/Money-Machine.git
cd Money-Machine
```

### Step 2: Deploy to Railway

1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your `Money-Machine` repo
4. Railway will auto-detect the Dockerfile and deploy

### Step 3: Add Databases (Railway Dashboard)

1. Click "New" → "Database" → "PostgreSQL"
2. Click "New" → "Database" → "Redis"
3. Railway auto-links them via environment variables

### Step 4: Configure Environment Variables

In Railway dashboard → Your n8n service → Variables:

```
# Required
N8N_ENCRYPTION_KEY=<random-32-char-string>
WEBHOOK_URL=https://your-app.railway.app

# Hunter Engine (pick at least one)
REDDIT_CLIENT_ID=<from reddit.com/prefs/apps>
REDDIT_CLIENT_SECRET=<from reddit.com/prefs/apps>

# Creator Engine  
PEXELS_API_KEY=<from pexels.com/api>
OPENAI_API_KEY=<optional, for script generation>

# Gatherer Engine (add as you set up channels)
YOUTUBE_CLIENT_ID=<from console.cloud.google.com>
YOUTUBE_CLIENT_SECRET=<from console.cloud.google.com>
YOUTUBE_REFRESH_TOKEN=<from OAuth flow>

# Survivor Engine (alerts)
TELEGRAM_BOT_TOKEN=<from @BotFather>
TELEGRAM_CHAT_ID=<your chat ID>
```

### Step 5: Import Workflows

1. Open n8n at `https://your-app.railway.app`
2. Go to Workflows → Import
3. Import all JSON files from `/workflows/` folder

### Step 6: Activate & Run

1. Enable each workflow
2. Watch the magic happen 🎉

---

## 📁 Project Structure

```
Money-Machine/
├── Dockerfile              # Elite n8n image with FFmpeg, Python
├── railway.json            # Railway deployment config
├── .env.template           # Environment variables template
│
├── engines/                # The 5 Core Engines
│   ├── __init__.py         # Central orchestrator
│   ├── hunter.py           # 🎯 Trend detection
│   ├── creator.py          # 🎨 Content creation
│   ├── gatherer.py         # 📡 Distribution
│   ├── businessman.py      # 💰 Finance management
│   └── survivor.py         # 🛡️ Self-healing
│
├── workflows/              # n8n Workflow Templates
│   ├── full_cycle.json     # Main automated loop
│   ├── daily_financial_report.json
│   ├── health_monitor.json
│   └── manual_create.json  # Webhook-triggered creation
│
└── docs/                   # Documentation
    ├── DEPLOYMENT.md
    ├── API_SETUP.md
    └── TROUBLESHOOTING.md
```

---

## 🔄 Automated Workflows

### 1. Full Cycle (Every 4 Hours)
```
Hunt → Create → Distribute → Track Financials → Health Check
```

### 2. Daily Financial Report (9 AM)
```
Calculate Revenue → Allocation → Send Telegram Report
```

### 3. Health Monitor (Every Hour)
```
Check Services → Check Errors → Alert if Degraded
```

### 4. Manual Create (Webhook)
```
POST /webhook/create-content
{
  "topic": "passive income ideas",
  "angle": "educational",
  "platforms": ["youtube", "tiktok"]
}
```

---

## 📊 Revenue Streams

### Tier 1: Fast Cash (Week 1-4)
- **Affiliate Links**: ClickBank, Digistore24, Amazon
- **Lead Gen**: CPA offers in video descriptions
- **Email Signups**: Beehiiv newsletter → future monetization

### Tier 2: Compounding (Month 2+)
- **YouTube AdSense**: Monetize at 1000 subs + 4000 hours
- **TikTok Creator Fund**: Monetize at 10K followers
- **Pinterest → Blog Traffic**: Long-term SEO

### Tier 3: Sovereign (Month 6+)
- **Digital Products**: Sell via Stripe payment links
- **Paid Newsletter**: Upgrade Beehiiv subscribers
- **Brand Deals**: Once you have reach

---

## 🛡️ Compliance & Safety

This system uses **OFFICIAL APIs ONLY**:

✅ YouTube Data API v3  
✅ TikTok Content Posting API  
✅ Meta Graph API (Instagram)  
✅ Pinterest API  
✅ Reddit API  
✅ Stripe API  

**No ToS violations. No browser automation of protected services.**

---

## 📈 Scaling the Machine

### Level 1: Single Instance ($5-20/mo)
- 1 n8n instance
- 6 YouTube uploads/day
- Basic monitoring

### Level 2: Amplifier Mode ($50-100/mo)
- Queue mode enabled
- Multiple worker nodes
- Higher throughput

### Level 3: Enterprise ($200+/mo)
- Dedicated resources
- Multiple channels per platform
- Advanced analytics

---

## 🔧 Troubleshooting

### "Rate Limit" Errors
The system auto-handles these. Check Survivor Engine logs.

### "Auth Failed"
Token expired. Re-run OAuth flow for that platform.

### Low Views / Shadowban Suspected
Survivor Engine monitors this. Rotate content angles or accounts.

### n8n Won't Start
Check Railway logs. Usually memory limits or missing env vars.

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch: `git checkout -b feature/amazing`
3. Commit: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing`
5. Open PR

---

## 📜 License

MIT License - Use it, modify it, profit from it.

---

## ⚠️ Disclaimer

This software is for educational purposes. The creator is not responsible for how you use it. Follow all platform Terms of Service and applicable laws.

---

**Built with 🔥 by the Money Machine Architecture**

*"It starts from free, becomes self-funding, and compounds forever."*
