# 🔑 API Setup Guide

Complete guide to setting up all FREE API credentials for the Money Machine.

---

## Quick Reference

| API | Free Tier | Setup Time | Required For |
|-----|-----------|------------|--------------|
| Reddit | 60 req/min | 5 min | Hunter Engine |
| Pexels | Unlimited | 2 min | Creator Engine |
| Edge TTS | Unlimited | 0 min | Creator Engine (built-in) |
| YouTube | 10K units/day | 15 min | Gatherer Engine |
| TikTok | Varies | 15 min | Gatherer Engine |
| Telegram | Unlimited | 5 min | Survivor Engine |
| Stripe | Pay per use | 10 min | Businessman Engine |
| Beehiiv | 2,500 subs | 5 min | Email Collection |
| OpenAI | $5 credit | 5 min | Script Generation (optional) |

---

## 🎯 Hunter Engine APIs

### Reddit API

**Free Tier:** 60 requests per minute

**Setup:**

1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Scroll down, click **"create another app..."**
3. Fill in the form:
   ```
   Name: MoneyMachine
   App type: script
   Description: Trend analysis tool
   About URL: (leave blank)
   Redirect URI: http://localhost:8080
   ```
4. Click **"create app"**
5. Note the credentials:
   - **Client ID**: The string under "personal use script"
   - **Client Secret**: The "secret" field

**Environment Variables:**
```bash
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=MoneyMachine/1.0
```

---

### Google Trends

**Free Tier:** No API, uses RSS feed (unlimited)

**Setup:** None required! The Hunter Engine uses the public RSS feed.

---

### Google Custom Search (Optional)

**Free Tier:** 100 queries/day

**Setup:**

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create new project or select existing
3. Enable **Custom Search API**
4. Go to **Credentials** → **Create API Key**
5. Go to [programmablesearchengine.google.com](https://programmablesearchengine.google.com)
6. Create a search engine
7. Get your **Search Engine ID**

**Environment Variables:**
```bash
GOOGLE_API_KEY=your_api_key
GOOGLE_CSE_ID=your_search_engine_id
```

---

## 🎨 Creator Engine APIs

### Edge TTS (Microsoft)

**Free Tier:** UNLIMITED (no API key needed)

**Setup:** Built into the Docker image. No configuration required!

**Available Voices:**
- `en-US-ChristopherNeural` (Male, US)
- `en-US-JennyNeural` (Female, US)
- `en-GB-RyanNeural` (Male, UK)
- `en-GB-SoniaNeural` (Female, UK)
- `en-AU-WilliamNeural` (Male, AU)

---

### Pexels Stock Video

**Free Tier:** UNLIMITED downloads

**Setup:**

1. Go to [pexels.com/api](https://www.pexels.com/api/)
2. Click **"Get Started"** or **"Your API Key"**
3. Create account if needed
4. Copy your API key

**Environment Variables:**
```bash
PEXELS_API_KEY=your_pexels_key
```

---

### Pixabay (Alternative)

**Free Tier:** UNLIMITED downloads

**Setup:**

1. Go to [pixabay.com/api/docs](https://pixabay.com/api/docs/)
2. Create account
3. Get API key from the docs page

**Environment Variables:**
```bash
PIXABAY_API_KEY=your_pixabay_key
```

---

### OpenAI (Optional - for script generation)

**Free Tier:** $5 credit on signup

**Setup:**

1. Go to [platform.openai.com](https://platform.openai.com)
2. Create account
3. Go to **API Keys** → **Create new secret key**
4. Copy the key (only shown once!)

**Environment Variables:**
```bash
OPENAI_API_KEY=sk-your-key-here
```

**Cost Optimization:**
- Use `gpt-4o-mini` model (cheapest)
- ~$0.01 per script generated
- $5 credit = ~500 scripts

---

### ElevenLabs (Premium TTS - Optional)

**Free Tier:** 10,000 characters/month

**Setup:**

1. Go to [elevenlabs.io](https://elevenlabs.io)
2. Create account
3. Go to Profile → API Key

**Environment Variables:**
```bash
ELEVENLABS_API_KEY=your_key
```

---

## 📡 Gatherer Engine APIs

### YouTube Data API v3

**Free Tier:** 10,000 quota units/day (~6 uploads)

**Setup:**

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create new project: `MoneyMachine`
3. Go to **APIs & Services** → **Library**
4. Search for **"YouTube Data API v3"** → **Enable**
5. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
6. Configure consent screen:
   - User Type: External
   - App name: Money Machine
   - Scopes: `youtube.upload`, `youtube.readonly`
7. Create OAuth 2.0 Client:
   - Type: Web application
   - Authorized redirect URIs: 
     - `https://your-app.railway.app/rest/oauth2-credential/callback`
8. Download JSON credentials

**Environment Variables:**
```bash
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_client_secret
```

**Getting Refresh Token:**
In n8n:
1. Go to **Credentials** → **New** → **YouTube OAuth2 API**
2. Enter Client ID and Secret
3. Click **"Connect my account"**
4. Authorize with your YouTube channel
5. n8n stores the refresh token automatically

---

### TikTok Content Posting API

**Free Tier:** Varies by region

**Setup:**

1. Go to [developers.tiktok.com](https://developers.tiktok.com)
2. Create developer account
3. Create new app
4. Apply for **Content Posting API** access
5. Wait for approval (can take days)

**Environment Variables:**
```bash
TIKTOK_CLIENT_KEY=your_client_key
TIKTOK_CLIENT_SECRET=your_client_secret
```

**Note:** TikTok API approval can take time. Start with YouTube while waiting.

---

### Pinterest API

**Free Tier:** Standard rate limits

**Setup:**

1. Go to [developers.pinterest.com](https://developers.pinterest.com)
2. Create developer account
3. Create new app
4. Get access token

**Environment Variables:**
```bash
PINTEREST_ACCESS_TOKEN=your_token
```

---

### Meta (Instagram) Graph API

**Free Tier:** Standard rate limits

**Requirements:**
- Facebook Business account
- Instagram Professional account (Creator or Business)
- Facebook Page linked to Instagram

**Setup:**

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Create new app → Business type
3. Add **Instagram Graph API** product
4. Get access token via Graph API Explorer

**Environment Variables:**
```bash
META_ACCESS_TOKEN=your_token
INSTAGRAM_BUSINESS_ID=your_ig_id
```

---

## 💰 Businessman Engine APIs

### Stripe

**Free Tier:** Only pay 2.9% + $0.30 per transaction

**Setup:**

1. Go to [dashboard.stripe.com](https://dashboard.stripe.com)
2. Create account
3. Go to **Developers** → **API Keys**
4. Copy **Secret key** (starts with `sk_`)

**Environment Variables:**
```bash
STRIPE_SECRET_KEY=sk_live_your_key
```

**Start with Test Mode:**
```bash
STRIPE_SECRET_KEY=sk_test_your_key
```

---

### PayPal

**Free Tier:** Only pay per transaction

**Setup:**

1. Go to [developer.paypal.com](https://developer.paypal.com)
2. Create app in **My Apps & Credentials**
3. Get Client ID and Secret

**Environment Variables:**
```bash
PAYPAL_CLIENT_ID=your_client_id
PAYPAL_CLIENT_SECRET=your_client_secret
```

---

### Mercury Banking (Optional)

**Free Tier:** Free business checking account

**Setup:**

1. Apply at [mercury.com](https://mercury.com)
2. Once approved, go to **Settings** → **API**
3. Generate API key

**Environment Variables:**
```bash
MERCURY_API_KEY=your_api_key
```

---

## 🛡️ Survivor Engine APIs

### Telegram Bot

**Free Tier:** UNLIMITED messages

**Setup:**

1. Open Telegram
2. Message [@BotFather](https://t.me/BotFather)
3. Send `/newbot`
4. Choose name: `Money Machine Bot`
5. Choose username: `moneymachine_yourname_bot`
6. Copy the **bot token**

**Get Chat ID:**

1. Send any message to your new bot
2. Visit: `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
3. Find `"chat":{"id":123456789}` in the response
4. Copy that ID

**Environment Variables:**
```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=your_chat_id
```

---

### Discord Webhook (Alternative to Telegram)

**Free Tier:** UNLIMITED messages

**Setup:**

1. In Discord, go to **Server Settings** → **Integrations**
2. Click **Webhooks** → **New Webhook**
3. Name it, choose channel, copy webhook URL

**Environment Variables:**
```bash
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
```

---

## 📧 Email Engine APIs

### Beehiiv

**Free Tier:** 2,500 subscribers

**Setup:**

1. Go to [beehiiv.com](https://www.beehiiv.com)
2. Create account
3. Create publication
4. Go to **Settings** → **Integrations** → **API**
5. Generate API key

**Environment Variables:**
```bash
BEEHIIV_API_KEY=your_api_key
BEEHIIV_PUBLICATION_ID=pub_xxxx
```

---

### ConvertKit (Alternative)

**Free Tier:** 1,000 subscribers

**Setup:**

1. Go to [convertkit.com](https://convertkit.com)
2. Create account
3. Go to **Settings** → **Advanced** → **API**

**Environment Variables:**
```bash
CONVERTKIT_API_KEY=your_api_key
```

---

## 🔗 Affiliate Network APIs

### ClickBank

**Free to Join**

**Setup:**

1. Sign up at [clickbank.com](https://www.clickbank.com)
2. Go to **Settings** → **Account Settings** → **API**
3. Generate API keys

**Environment Variables:**
```bash
CLICKBANK_ACCOUNT_NAME=your_nickname
CLICKBANK_API_KEY=your_api_key
```

---

### Digistore24

**Free to Join**

**Setup:**

1. Sign up at [digistore24.com](https://www.digistore24.com)
2. Go to Account settings for API access

**Environment Variables:**
```bash
DIGISTORE_API_KEY=your_api_key
```

---

## ✅ Verification Checklist

After setup, verify each API:

```bash
# Test in n8n Execute Command node:

# Reddit
python3 -c "from engines.hunter import RedditHunter; import asyncio; h = RedditHunter(); print(asyncio.run(h.authenticate()))"

# Pexels
python3 -c "from engines.creator import StockEngine; import asyncio; s = StockEngine(); print(asyncio.run(s.search_pexels_videos('nature')))"

# Telegram
python3 -c "from engines.survivor import AlertManager; import asyncio; a = AlertManager(); print(asyncio.run(a.send_telegram('Test!', 'info')))"
```

---

## 🚨 Common Issues

### "Invalid API Key"
- Double-check copy/paste (no extra spaces)
- Verify correct environment (test vs live)
- Check if key has required permissions

### "Rate Limit Exceeded"
- Survivor Engine handles this automatically
- Wait for reset (usually 24 hours)
- Consider upgrading if persistent

### "OAuth Token Expired"
- Re-authorize in n8n credentials
- Tokens refresh automatically for most APIs

---

**All APIs configured? You're ready to run the Money Machine! 🚀**
