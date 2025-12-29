# ===========================================================
# ANOINTMENT SYSTEM — FINAL EXECUTION CHECKLIST
# ===========================================================
# Print this. Pin it. You're done configuring after this.
# ===========================================================

## 🟢 INFRASTRUCTURE STATUS

### CONTROL LAYER ($0/month)
- [ ] Google Sheet created with all 6 tabs:
  - [ ] Queue (id, brand, title, script, status, video_url, created_at, posted_at)
  - [ ] Error_Log (timestamp, workflow, node, error_message, healer_response, resolved)
  - [ ] Brands (name, platform, page_id, access_token, ig_user_id, active)
  - [ ] Music_Bank (id, name, google_drive_url, mood, duration_sec, used_count, last_used)
  - [ ] Analytics (date, brand, videos_posted, views, revenue_est)
  - [ ] Flood_Log (id, source_url, remixed_url, posted_to, posted_at, views)
- [ ] Glide app connected to sheet
- [ ] Share sheet with n8n service account email

### ORCHESTRATION LAYER (~$8/month)
- [ ] Railway account: https://railway.app
- [ ] n8n deployed via Railway template
- [ ] Custom domain configured (optional)
- [ ] Import workflows:
  - [ ] n8n_anointment_original.json
  - [ ] n8n_anointment_flood.json
  - [ ] n8n_anointment_error_handler.json

### INTELLIGENCE LAYER (~$5/month)
- [ ] Apify account: https://apify.com
- [ ] Actors deployed:
  - [ ] anointment/the-perfect-prompt-generator
  - [ ] anointment/the-ai-workflow-auto-healer
  - [ ] anointment/tiktok-viral-predictor (for flood)
  - [ ] anointment/ig-reel-scraper (for flood)

### RENDERING LAYER (~$15/month)
- [ ] Creatomate account: https://creatomate.com
- [ ] API key obtained
- [ ] Templates created for each brand:
  - [ ] money_machine_template
  - [ ] solidarity_template
  - [ ] youtube_template_1/2/3

### MUSIC LAYER ($0 ongoing)
- [ ] Suno songs generated (batch of 50+)
- [ ] Uploaded to Google Drive folder
- [ ] Folder shared with "anyone with link"
- [ ] Each track added to Music_Bank sheet

---

## 🔑 ENVIRONMENT VARIABLES CHECKLIST

Set these in Railway → n8n → Variables:

### Core
```
OPENAI_API_KEY=sk-...
APIFY_TOKEN=apify_api_...
CREATOMATE_API_KEY=...
GOOGLE_SHEET_ID=...
```

### Money Machine AI
```
MM_FB_PAGE_ID=...
MM_FB_ACCESS_TOKEN=...
MM_IG_USER_ID=...
```

### Solidarity Ointments
```
SOL_FB_PAGE_ID=...
SOL_FB_ACCESS_TOKEN=...
SOL_IG_USER_ID=...
```

### RAWSCROLL (Flood)
```
RAW_FB_PAGE_ID=...
RAW_FB_ACCESS_TOKEN=...
RAW_IG_USER_ID=...
```

### OnTheDaily (Flood)
```
OTD_FB_PAGE_ID=...
OTD_FB_ACCESS_TOKEN=...
OTD_IG_USER_ID=...
```

### YouTube (3 Channels)
```
YT_CHANNEL_1_REFRESH_TOKEN=...
YT_CHANNEL_2_REFRESH_TOKEN=...
YT_CHANNEL_3_REFRESH_TOKEN=...
YT_CLIENT_ID=...
YT_CLIENT_SECRET=...
```

### Alerts
```
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
ALERT_EMAIL=...
```

### Railway Remix Engine
```
REMIX_ENGINE_URL=https://your-app.railway.app
```

---

## 📊 CONTENT TRACKS

### TRACK 1: ORIGINAL CONTENT
| Brand | Platform | Cost/Video | Daily Target |
|-------|----------|------------|--------------|
| Money Machine AI | FB + IG | $0.40-$1.20 | 1 |
| Solidarity Ointments | FB + IG | $0.40-$1.20 | 1 |
| YouTube Channel 1 | YouTube | $0.50-$1.50 | 0.5 |
| YouTube Channel 2 | YouTube | $0.50-$1.50 | 0.5 |
| YouTube Channel 3 | YouTube | $0.50-$1.50 | 0.5 |

### TRACK 2: FLOOD CONTENT
| Brand | Platform | Cost/Video | Daily Target |
|-------|----------|------------|--------------|
| RAWSCROLL | FB + IG | $0.03-$0.07 | 6 |
| OnTheDaily | FB + IG | $0.03-$0.07 | 6 |

---

## 🎵 SUNO MUSIC BANK

Pre-generate these tracks:

### Moods (10 each)
- [ ] Hype/Energetic
- [ ] Chill/Ambient
- [ ] Dramatic/Cinematic
- [ ] Motivational
- [ ] Dark/Mysterious

### File Naming Convention
```
suno_[mood]_[number]_[bpm].mp3
Example: suno_hype_003_120.mp3
```

### Google Drive Structure
```
Suno_Music_Bank/
├── hype/
│   ├── suno_hype_001_128.mp3
│   └── ...
├── chill/
├── dramatic/
├── motivational/
└── dark/
```

---

## 🚨 ERROR HANDLING FLOW

```
Error Occurs in n8n
        ↓
Error Handler Workflow Triggered
        ↓
Auto-Healer Actor Called (Apify)
        ↓
Healer Returns Diagnosis + Fix
        ↓
Telegram Alert Sent
        ↓
Error Logged to Sheet
        ↓
Manual Fix Applied (if needed)
        ↓
Mark Resolved in Sheet
```

---

## 📅 DAILY OPERATIONS

### Morning (Manual - 5 min)
1. Check Error_Log sheet for unresolved errors
2. Review Analytics sheet
3. Queue 2 original videos in Queue sheet

### Automatic (24/7)
- Original workflow: Processes Queue sheet entries
- Flood workflow: Runs every 4 hours
- Error handler: Monitors all workflows

### Weekly (15 min)
1. Replenish Music_Bank if tracks running low
2. Review flood performance in Flood_Log
3. Adjust Apify actor settings if needed

---

## 💰 MONTHLY BUDGET

| Service | Cost |
|---------|------|
| Railway (n8n) | ~$8 |
| Apify | ~$5 |
| Creatomate | ~$15 |
| OpenAI | ~$5-10 |
| **TOTAL** | **$33-38** |

Max ceiling with heavy usage: $72/month

---

## 🟢 ACTIVATION SEQUENCE

1. Verify all environment variables set
2. Test each workflow manually:
   - Add test entry to Queue sheet
   - Run original workflow manually
   - Confirm video posted
3. Enable workflow schedules:
   - Original: Triggered by sheet updates
   - Flood: Every 4 hours
4. Monitor for 24 hours
5. You're live 🚀

---

## ⚠️ COMMON ISSUES

### "422 Unprocessable Entity"
**Cause:** Double JSON serialization in n8n HTTP node
**Fix:** Use `{{ $json.field }}` not `{{ JSON.stringify($json.field) }}`

### "Instagram cross-posting failed"
**Cause:** share_to_facebook unreliable
**Fix:** Parallel post to IG and FB separately (already configured)

### "Rate limit exceeded"
**Cause:** Too many API calls
**Fix:** Increase delay between posts in workflow

### "Video not rendering"
**Cause:** Creatomate template mismatch
**Fix:** Check template variables match workflow output

---

## 🔒 SECURITY REMINDERS

- [ ] Rotate API keys every 90 days
- [ ] Use Railway environment variables (never hardcode)
- [ ] Set Glide app to private
- [ ] Monitor Apify usage for anomalies

---

**You are done.**

Print this. Pin it. Operate.

No more setup.
No more theory.
No more gray areas.

The system runs. You scale.
