# 🚀 Deployment Guide

Complete step-by-step guide to deploy the Money Machine on Railway.

---

## Prerequisites

Before you start, you'll need:

1. **GitHub Account** - To host your code
2. **Railway Account** - Free tier works to start
3. **$5-50** - First month's budget (will become self-funding)

---

## Phase 1: Railway Setup (10 minutes)

### Step 1.1: Create Railway Account

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. You get **$5 free credit** on signup

### Step 1.2: Create New Project

1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Authorize Railway to access your GitHub
4. Select your **Money-Machine** repository
5. Click **Deploy**

Railway will:
- Detect the Dockerfile
- Build the custom n8n image
- Deploy it automatically

### Step 1.3: Add PostgreSQL Database

1. In your Railway project, click **"New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Wait for it to provision (~30 seconds)
4. Railway automatically links it via `DATABASE_URL`

### Step 1.4: Add Redis (for Queue Mode)

1. Click **"New"** again
2. Select **"Database"** → **"Redis"**
3. Wait for it to provision
4. Railway automatically links via `REDIS_URL`

### Step 1.5: Configure Domain

1. Click on your n8n service
2. Go to **Settings** → **Networking**
3. Click **"Generate Domain"**
4. Note your URL: `https://your-app-name.railway.app`

---

## Phase 2: Environment Variables (5 minutes)

### Step 2.1: Core Variables

In Railway dashboard → Your service → **Variables** tab:

```bash
# ============ REQUIRED ============
N8N_ENCRYPTION_KEY=generate-a-random-32-character-string-here
N8N_HOST=0.0.0.0
N8N_PORT=5678
N8N_PROTOCOL=https
WEBHOOK_URL=https://your-app-name.railway.app

# Queue Mode (for scaling)
EXECUTIONS_MODE=queue
```

### Step 2.2: Generate Encryption Key

Run this in terminal to generate a key:

```bash
# Windows PowerShell
-join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})

# Or just use any password manager to generate 32 random chars
```

---

## Phase 3: API Credentials (20 minutes)

### 3.1 Reddit API (FREE - Hunter Engine)

1. Go to [reddit.com/prefs/apps](https://reddit.com/prefs/apps)
2. Click **"create another app..."**
3. Fill in:
   - Name: `MoneyMachine`
   - Type: `script`
   - Redirect URI: `http://localhost:8080`
4. Copy the **client ID** (under app name) and **secret**

```bash
REDDIT_CLIENT_ID=your-client-id
REDDIT_CLIENT_SECRET=your-client-secret
REDDIT_USER_AGENT=MoneyMachine/1.0
```

### 3.2 Pexels API (FREE - Creator Engine)

1. Go to [pexels.com/api](https://www.pexels.com/api/)
2. Click **"Get Started"**
3. Create account and get API key

```bash
PEXELS_API_KEY=your-pexels-key
```

### 3.3 OpenAI API (OPTIONAL - $5 free credit)

1. Go to [platform.openai.com](https://platform.openai.com)
2. Create account
3. Go to API Keys → Create new key

```bash
OPENAI_API_KEY=your-openai-key
```

### 3.4 Telegram Bot (FREE - Survivor Engine Alerts)

1. Open Telegram, message [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow prompts, get your **bot token**
4. Message your bot once, then visit:
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
5. Find your **chat_id** in the response

```bash
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

### 3.5 YouTube API (FREE - Gatherer Engine)

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create new project: `MoneyMachine`
3. Enable **YouTube Data API v3**
4. Go to **Credentials** → **Create OAuth 2.0 Client**
5. Application type: **Web application**
6. Authorized redirect URI: `https://your-app.railway.app/rest/oauth2-credential/callback`
7. Download JSON, note client ID and secret

```bash
YOUTUBE_CLIENT_ID=your-client-id
YOUTUBE_CLIENT_SECRET=your-client-secret
```

**To get Refresh Token:**
1. In n8n, add YouTube OAuth2 credential
2. Click "Connect"
3. Authorize with your YouTube channel
4. n8n stores the refresh token automatically

---

## Phase 4: Import Workflows (5 minutes)

### Step 4.1: Access n8n

1. Open your Railway URL: `https://your-app.railway.app`
2. Create admin account on first visit
3. You're now in the n8n dashboard

### Step 4.2: Import Workflows

For each file in `/workflows/`:

1. Click **Workflows** → **Import from File**
2. Upload the JSON file
3. Click **Import**

Import order:
1. `full_cycle.json` - Main automated loop
2. `daily_financial_report.json` - Financial tracking
3. `health_monitor.json` - System monitoring
4. `manual_create.json` - Webhook trigger

### Step 4.3: Configure Credentials

In n8n → **Credentials**:

1. Add **Telegram API** credential with your bot token
2. Add **YouTube OAuth2** credential and connect
3. Add any other platform credentials

### Step 4.4: Activate Workflows

For each workflow:
1. Open it
2. Toggle **Active** to ON
3. Save

---

## Phase 5: Verify Deployment (5 minutes)

### Step 5.1: Test Health Check

```bash
curl https://your-app.railway.app/healthz
```

Should return: `{ "status": "ok" }`

### Step 5.2: Test Webhook

```bash
curl -X POST https://your-app.railway.app/webhook/create-content \
  -H "Content-Type: application/json" \
  -d '{"topic": "test topic", "angle": "educational"}'
```

### Step 5.3: Check Telegram

You should receive a test alert if everything is configured correctly.

### Step 5.4: Monitor Logs

In Railway dashboard:
1. Click your n8n service
2. Go to **Deployments** → **View Logs**
3. Watch for any errors

---

## Phase 6: First Content Run (Manual Test)

### Step 6.1: Trigger Hunter

In n8n:
1. Open the **Full Cycle** workflow
2. Click **Execute Workflow**
3. Watch it run through all engines

### Step 6.2: Check Outputs

After execution:
1. Check `/data/output/` for generated videos
2. Check Telegram for status updates
3. Check Railway logs for any errors

---

## Scaling Guide

### When to Scale

| Signal | Action |
|--------|--------|
| CPU > 80% consistently | Add worker nodes |
| Queue backing up | Enable queue mode |
| Memory exhausted | Upgrade Railway plan |
| Rate limits hit | Add more accounts |

### How to Add Worker Nodes

1. In Railway, click **"New"** → **"Empty Service"**
2. Connect same GitHub repo
3. Add environment variable: `N8N_WORKER=true`
4. Deploy

Workers will automatically pick up jobs from Redis queue.

---

## Cost Optimization

### Stay Under $50/month

1. **Use free tiers first** - Don't upgrade until needed
2. **Sleep during low hours** - Use Railway's scaling features
3. **Batch operations** - Group API calls to reduce overhead
4. **Cache aggressively** - Reuse stock footage

### When Revenue > Costs

The Businessman Engine will automatically:
1. Track all revenue streams
2. Allocate 40% to reinvestment
3. Suggest infrastructure upgrades

---

## Backup Strategy

### Export Workflows

Regularly:
1. Go to n8n → Workflows
2. Select all
3. Export to JSON
4. Store in your repo

### Database Backups

Railway provides automatic backups for PostgreSQL. Enable in:
Settings → Database → Backups

---

## Troubleshooting

### n8n Won't Start

1. Check Railway logs
2. Verify all required env vars are set
3. Check if database is connected

### Workflows Not Running

1. Verify workflows are active
2. Check n8n execution logs
3. Verify webhook URLs are correct

### No Content Created

1. Check Hunter is finding opportunities
2. Verify Creator has stock footage access
3. Check FFmpeg logs for errors

### API Rate Limits

The Survivor Engine handles this automatically. Check:
1. Telegram for rate limit alerts
2. n8n error logs
3. Circuit breaker status

---

## Next Steps

1. ✅ Deploy to Railway
2. ✅ Configure all APIs
3. ✅ Import and activate workflows
4. ⏳ Run first content cycle
5. ⏳ Set up YouTube channel
6. ⏳ Connect affiliate accounts
7. ⏳ Watch the money flow

---

**You're now running the Money Machine! 🎉**

*Check back daily, review Telegram reports, and watch your autonomous revenue engine grow.*
