# 💎 Money Machine AI - Elite Production System

## 📊 System Summary (December 25, 2025)

### 🎯 What Is This?
An **autonomous YouTube Shorts factory** that creates wealth/finance videos 24/7:
- AI-generated scripts (GPT-4o-mini)
- Premium voice synthesis (ElevenLabs/Edge-TTS)
- Scene-based video assembly with B-roll matching
- Auto-upload to YouTube with SEO-optimized metadata

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         MONEY MACHINE AI                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │  🧠 AAVE     │───▶│  📝 Script   │───▶│  🎙️ Voice   │              │
│  │  Brain       │    │  Generator   │    │  Synthesis   │              │
│  │  (Topics)    │    │  (GPT-4o)    │    │  (11Labs)    │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│         │                                        │                      │
│         │         ┌──────────────┐               │                      │
│         └────────▶│  🎬 Elite    │◀──────────────┘                      │
│                   │  Builder     │                                      │
│                   │  (FFmpeg)    │                                      │
│                   └──────────────┘                                      │
│                          │                                              │
│         ┌────────────────┼────────────────┐                            │
│         ▼                ▼                ▼                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                   │
│  │  📤 YouTube  │ │  📊 Airtable │ │  📱 Telegram │                   │
│  │  Upload      │ │  Logging     │ │  Alerts      │                   │
│  └──────────────┘ └──────────────┘ └──────────────┘                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start Options

### Option 1: Local Python (Recommended)
```bash
# Single elite video
python AUTO_ELITE.py --once

# Continuous production (1/hour)
python AUTO_ELITE.py

# Fast mode (1/30 min)
python AUTO_ELITE.py --fast

# Custom topic
python AUTO_ELITE.py --topic "Why Banks Want You Broke"
```

### Option 2: n8n Workflow (Cloud)
1. Import `workflows/n8n_elite_autonomous.json` to n8n Cloud
2. Configure credentials (OpenAI, ElevenLabs, Google Drive, Shotstack)
3. Enable the schedule trigger
4. Monitor via Telegram alerts

### Option 3: Legacy Scripts
```bash
python LIVE.py          # Original continuous mode
python ELITE_RUN.py     # Blocking single run
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `AUTO_ELITE.py` | **NEW** - Main autonomous production script |
| `LIVE.py` | Continuous mode launcher |
| `ELITE_RUN.py` | Single video production |
| `workflows/n8n_elite_autonomous.json` | **NEW** - Elite n8n workflow |
| `workflows/continuous_mode.py` | Core production logic |
| `engines/aave_engine.py` | AAVE Brain - weighted topic selection |
| `engines/elite_builder.py` | Scene-based video assembly |
| `engines/uploaders.py` | YouTube/TikTok/Instagram uploaders |

---

## 🔧 Configuration (.env)

### Required API Keys
```env
# AI Content Generation
OPENAI_API_KEY=sk-proj-xxx          # Script generation
ELEVENLABS_API_KEY=xxx              # Premium voice (optional)

# YouTube Upload
YOUTUBE_CLIENT_ID=xxx
YOUTUBE_CLIENT_SECRET=xxx
YOUTUBE_REFRESH_TOKEN=xxx
YOUTUBE_CHANNEL_ID=UCZppwcvPrWlAG0vb78elPJA

# Shotstack (Cloud Video Rendering)
SHOTSTACK_API_KEY=sofi4GJNxp6XncLw3t46Cqe4n73lDAd09wrd3JIV
SHOTSTACK_OWNER_ID=fhsbdmsug8

# Notifications
TELEGRAM_BOT_TOKEN=xxx
TELEGRAM_CHAT_ID=5033650061
```

### n8n Credential IDs
- OpenAI: `tgF2FazdNfVR1lMh`
- ElevenLabs: `pD7r1ApG2XA4ZVxB`
- Google Drive: `lQp7tCjjzrwFF2uj`
- Telegram: `mYboMwTFDnzlHNuv`
- Airtable: `appQQycFmxyiQKk44`

---

## 🧠 AAVE Brain - Topic Selection

**Algorithm-Adaptive Visual Evolution** - Topics are weighted by:
1. Historical performance
2. Hook type effectiveness
3. Visual intent matching
4. Time-based rotation

### Elite Topic Pool (15 Topics)
| Topic | Priority | Hook Type |
|-------|----------|-----------|
| Why the Rich Use Debt as a Weapon | 95 | threat |
| The Fed Just Changed Everything | 94 | urgency |
| Why the Middle Class is Disappearing | 93 | system_exposure |
| The Hidden Tax Stealing Your Wealth | 92 | conspiracy_adjacent |
| The Psychology of Why You Stay Poor | 91 | self_attack |
| Why Banks Want You Broke | 90 | victim_awakening |
| The Wealth Transfer Happening Now | 89 | future_threat |
| The 3 Money Lies From School | 88 | myth_destruction |
| How the 1% Think Differently | 88 | power_gap |
| How I Save 50% Automatically | 87 | authority_gap |
| Investing at 20 vs 40 | 86 | loss_framing |
| The Credit Card Hack Banks Hate | 85 | contrarian_fear |
| Why Savings Accounts Lose Money | 84 | harsh_truth |
| Why I Stopped Using Savings | 83 | identity_trigger |
| The Real Reason College is Expensive | 82 | moral_shock |

---

## 📊 Current Status

### Video Inventory
- **Location**: `data/output/`
- **Latest Videos**: ~33-36 MB each (high quality)
- **Format**: 1080x1920 (9:16 portrait), 30fps, H.264

### Recent Uploads (December 24-25, 2025)
- ✅ 9 videos uploaded to YouTube
- ✅ Channel: Money Machine AI
- ✅ Quality: Elite scene-based assembly

### System Health
- ✅ OpenAI API: Connected
- ✅ YouTube OAuth: Configured
- ✅ Edge-TTS: Functional
- ✅ FFmpeg: Installed
- ⚠️ Continuous automation: Stopped (restart with `python AUTO_ELITE.py`)

---

## 🔄 n8n Workflow Nodes

### Elite Autonomous Pipeline
```
⏰ Hourly Production ──┐
                       ├──▶ 🧠 AAVE Brain ──▶ 📝 Elite Script ──▶ ⚡ Processor
🎯 Manual Trigger ─────┘
                                                                      │
                       ┌──────────────────────────────────────────────┘
                       ▼
                  🎙️ ElevenLabs ──▶ ☁️ Save to Drive ──▶ 🎬 Shotstack
                                                              │
                       ┌──────────────────────────────────────┘
                       ▼
                  ⏳ Wait ──▶ 📊 Check Status ──▶ ✅ Complete?
                                                      │
                       ┌────────────────Yes───────────┤────No────┐
                       ▼                                         ▼
              📋 YouTube Metadata                           ⚠️ Error Alert
                       │
           ┌───────────┴───────────┐
           ▼                       ▼
      📱 Success Alert       📊 Log to Airtable
```

---

## 📈 Next Steps

1. **Start Production**: `python AUTO_ELITE.py`
2. **Import n8n Workflow**: Upload `n8n_elite_autonomous.json`
3. **Monitor**: Check Telegram for alerts
4. **Track Performance**: Review Airtable logs
5. **Evolve**: AAVE will auto-adjust topic weights based on views

---

## 🛠️ Troubleshooting

### Videos not uploading?
```bash
# Check YouTube credentials
python -c "from engines.uploaders import YouTubeUploader; u = YouTubeUploader(); print(u.is_configured())"
```

### TTS failing?
```bash
# Test edge-tts
python -c "import asyncio; import edge_tts; asyncio.run(edge_tts.Communicate('Test', 'en-US-AndrewNeural').save('test.mp3'))"
```

### n8n workflow not triggering?
- Check schedule is enabled (not disabled)
- Verify webhook URL is accessible
- Check credential connections

---

## 📞 Integration Points

| Service | Endpoint | Purpose |
|---------|----------|---------|
| n8n Cloud | `https://anointment.app.n8n.cloud` | Workflow orchestration |
| Shotstack | `https://api.shotstack.io/v1/render` | Cloud video rendering |
| YouTube | Data API v3 | Video uploads |
| ElevenLabs | `v1/text-to-speech` | Premium voice |
| Telegram | Bot API | Alerts & notifications |
| Airtable | `appQQycFmxyiQKk44` | DNA tracking |
| Google Drive | Folder `1BGGyx_C-Yv1m_v-fmC2aJj3Yp_c8IJ6Y` | Audio storage |

---

*Last updated: December 25, 2025*
*System Version: Elite v3.0*
