# Money Machine – Railway Deployment Guide

> **Status**: Production-Ready  
> **Estimated Deploy Time**: 15 minutes  
> **Monthly Cost**: ~$12-15 (self-funding after first revenue)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        RAILWAY PROJECT                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   App       │  │  PostgreSQL │  │         Redis           │  │
│  │  (Docker)   │  │   (DB)      │  │       (Queue)           │  │
│  │             │  │             │  │                         │  │
│  │  - n8n      │  │  - Metrics  │  │  - Job Queue            │  │
│  │  - Engines  │  │  - Events   │  │  - Session Cache        │  │
│  │  - API      │  │  - Learning │  │  - Rate Limiting        │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Pre-Deployment Checklist

### Required API Keys

| Service | Required | How to Get |
|---------|----------|------------|
| Reddit | ✅ | https://www.reddit.com/prefs/apps |
| Pexels | ✅ | https://www.pexels.com/api/ |
| YouTube | ✅ | https://console.cloud.google.com |
| Telegram | ✅ | https://t.me/BotFather |
| OpenAI | ⚪ Optional | https://platform.openai.com |
| ElevenLabs | ⚪ Optional | https://elevenlabs.io |
| Stripe | ⚪ Optional | https://dashboard.stripe.com |
| PayPal | ⚪ Optional | https://developer.paypal.com |
| ClickBank | ⚪ Optional | https://accounts.clickbank.com |
| Systeme.io | ⚪ Optional | https://systeme.io |

### Local Requirements

- [ ] Git installed
- [ ] Docker installed (for local testing)
- [ ] Railway CLI installed (optional)
- [ ] All API keys collected

---

## 🚀 Deployment Steps

### Step 1: Create Railway Project

1. Go to https://railway.app
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Connect GitHub and select `Money-Machine` repo
5. Railway will auto-detect Dockerfile

### Step 2: Add PostgreSQL

1. In Railway dashboard, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Wait for provisioning (~30 seconds)
4. Copy the `DATABASE_URL` from Variables tab

### Step 3: Add Redis

1. Click **"+ New"** again
2. Select **"Database"** → **"Redis"**
3. Wait for provisioning
4. Copy the `REDIS_URL` from Variables tab

### Step 4: Configure Environment Variables

In the **App service** → **Variables** tab, add:

```env
# ============================================
# REQUIRED - Core Infrastructure
# ============================================
N8N_ENCRYPTION_KEY=your-32-character-random-string
WEBHOOK_URL=https://your-app-name.up.railway.app
DATABASE_URL=<auto-injected by Railway>
REDIS_URL=<auto-injected by Railway>

# ============================================
# REQUIRED - Content APIs
# ============================================
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
PEXELS_API_KEY=your_pexels_api_key
PIXABAY_API_KEY=your_pixabay_api_key

# ============================================
# REQUIRED - Distribution
# ============================================
YOUTUBE_CLIENT_ID=your_youtube_client_id
YOUTUBE_CLIENT_SECRET=your_youtube_client_secret
YOUTUBE_REFRESH_TOKEN=your_youtube_refresh_token

# ============================================
# REQUIRED - Notifications
# ============================================
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# ============================================
# OPTIONAL - AI Enhancement
# ============================================
OPENAI_API_KEY=your_openai_key
ELEVENLABS_API_KEY=your_elevenlabs_key

# ============================================
# OPTIONAL - Monetization
# ============================================
STRIPE_API_KEY=your_stripe_key
PAYPAL_CLIENT_ID=your_paypal_id
PAYPAL_CLIENT_SECRET=your_paypal_secret
CLICKBANK_CLERK_KEY=your_clickbank_key
SYSTEME_API_KEY=your_systeme_key

# ============================================
# OPTIONAL - Advanced
# ============================================
SWEEP_DESTINATION_EMAIL=your_paypal_email
MERCURY_ACCOUNT_ID=your_mercury_id
```

### Step 5: Initialize Database

After deployment, run the schema:

```bash
# Via Railway CLI
railway run psql $DATABASE_URL < db/schema.sql

# Or via Railway Dashboard → Database → Query tab
# Paste contents of db/schema.sql
```

### Step 6: Import n8n Workflows

1. Access n8n at `https://your-app.up.railway.app`
2. Go to **Workflows** → **Import**
3. Import these files from `/workflows/`:
   - `omni_orchestrator.json`
   - `lead_gen_orchestrator.json`
   - `finance_sweeper.json`
   - `health_monitor.json`

### Step 7: Activate Workflows

1. Open each imported workflow
2. Click **"Activate"** toggle (top right)
3. Verify green indicator shows "Active"

### Step 8: Test System

1. Trigger manual test:
```bash
curl -X POST https://your-app.up.railway.app/webhook/test \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

2. Check Telegram for "System Online" message
3. Verify no errors in Railway logs

---

## 📊 Post-Deployment Verification

### Health Checks

| Check | Expected | Action if Failed |
|-------|----------|------------------|
| App running | Green status | Check logs |
| PostgreSQL connected | Tables exist | Re-run schema.sql |
| Redis connected | Ping success | Check REDIS_URL |
| n8n accessible | Login page loads | Check WEBHOOK_URL |
| Telegram alerts | Message received | Verify bot token |

### First 24 Hours

- [ ] Monitor Railway logs for errors
- [ ] Verify cron jobs trigger on schedule
- [ ] Check database for new records
- [ ] Confirm Telegram reports arrive

---

## 🔧 Troubleshooting

### Common Issues

**App won't start**
```bash
# Check logs
railway logs

# Common fixes:
# - Missing env variable
# - Docker build failed
# - Port conflict
```

**Database connection failed**
```bash
# Verify DATABASE_URL is set
railway variables

# Test connection
railway run psql $DATABASE_URL -c "SELECT 1"
```

**n8n workflows not triggering**
- Ensure workflows are activated
- Check webhook URLs match WEBHOOK_URL env var
- Verify cron schedules are correct

**No Telegram notifications**
```bash
# Test bot directly
curl "https://api.telegram.org/bot<TOKEN>/sendMessage?chat_id=<CHAT_ID>&text=Test"
```

---

## 📈 Scaling

### Horizontal Scaling (When Revenue > $500/mo)

```json
// railway.json
{
  "deploy": {
    "numReplicas": 2,
    "healthcheck": {
      "path": "/health",
      "interval": 30
    }
  }
}
```

### Redis Queue Mode

Enable queue mode for n8n when running multiple replicas:

```env
EXECUTIONS_MODE=queue
QUEUE_BULL_REDIS_HOST=<redis-host>
```

---

## 🛡️ Security Best Practices

1. **Never commit .env files** - Use Railway variables
2. **Rotate API keys quarterly** - Set calendar reminder
3. **Enable 2FA** on all platforms (Railway, GitHub, YouTube)
4. **Monitor for anomalies** - Set up Telegram alerts for unusual activity
5. **Use read-only tokens** where possible

---

## 💰 Cost Optimization

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| Railway | $5/mo credit | ~$10/mo |
| PostgreSQL | 500MB | Included |
| Redis | 100MB | Included |
| YouTube API | 10,000 units/day | N/A |
| Pexels | 200 req/hr | N/A |

**Target**: System self-funds by Week 3-4

---

## 🔄 Maintenance Schedule

| Task | Frequency | Automated? |
|------|-----------|------------|
| Health check | Every 5 min | ✅ |
| Log rotation | Daily | ✅ |
| DB backup | Daily | ✅ (Railway) |
| API key rotation | Quarterly | ❌ Manual |
| Dependency updates | Monthly | ❌ Manual |

---

## 📞 Support

- **Railway Docs**: https://docs.railway.app
- **n8n Docs**: https://docs.n8n.io
- **GitHub Issues**: Create issue in repo

---

*Last Updated: December 2025*
