# 🔱 ANOINTMENT SYSTEM — A→Z SETUP GUIDE

> **Time Required:** 65 minutes total  
> **Result:** Posting from your phone TODAY

---

## PRE-REQUISITES ✅

| Layer | Status |
|-------|--------|
| n8n on Railway | ✅ DONE |
| Apify Actors | ✅ DONE |
| remix_engine.py | ✅ DONE |
| Suno Music Bank | ✅ DONE |

---

## PART 1 — GOOGLE SHEETS (15 min)

### Step 1.1 — Create Master Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create new sheet
3. Name it **exactly**: `ANOINTMENT_COMMAND`

### Step 1.2 — Create 6 Tabs

At the bottom, create tabs with **EXACT names** (case-sensitive):

```
Queue
Flood_Log
Error_Log
Music_Bank
Brands
Analytics
```

### Step 1.3 — Configure Each Tab

#### 📌 Queue (Original Content)

| Column | Purpose |
|--------|---------|
| id | Auto-generated |
| brand | Money Machine / Solidarity / etc. |
| title | Video title |
| topic | Content topic |
| script | Generated script |
| status | pending → processing → posted |
| video_url | Final rendered URL |
| created_at | Timestamp |
| posted_at | When posted |

**Row 1 headers (copy exactly):**
```
id	brand	title	topic	script	status	video_url	created_at	posted_at
```

#### 📌 Flood_Log (Repurposed Content)

```
id	source_platform	source_url	remixed_url	brand	posted_to	posted_at	views
```

#### 📌 Error_Log

```
timestamp	workflow	node	error_message	healer_response	resolved
```

#### 📌 Music_Bank

```
id	name	google_drive_url	mood	duration_sec	used_count	last_used
```

#### 📌 Brands

```
name	platform	page_id	ig_user_id	access_token	active
```

**Sample rows:**
| name | platform | page_id | ig_user_id | access_token | active |
|------|----------|---------|------------|--------------|--------|
| Money Machine | instagram | - | 17841... | EAA... | TRUE |
| Money Machine | facebook | 123456... | - | EAA... | TRUE |
| RAWSCROLL | instagram | - | 17841... | EAA... | TRUE |
| RAWSCROLL | facebook | 789012... | - | EAA... | TRUE |

#### 📌 Analytics

```
date	brand	videos_posted	views	revenue_est
```

### Step 1.4 — Share Sheet with n8n

1. Click **Share** button
2. Add your n8n service account email (from Google Cloud)
3. Give **Editor** access

✅ **SHEETS DONE — DO NOT PROCEED UNTIL COMPLETE**

---

## PART 2 — GLIDE APP (20 min)

### Step 2.1 — Create App

1. Go to [glideapps.com](https://www.glideapps.com)
2. Click **New App**
3. Choose **Google Sheets**
4. Select `ANOINTMENT_COMMAND`
5. App name: `Anointment Control`

### Step 2.2 — Build Input Form

1. Open **Queue** tab in Glide
2. Change layout → **Form**
3. Add fields:

| Field | Type |
|-------|------|
| brand | Choice |
| topic | Text |
| title | Text (optional) |

### Step 2.3 — Configure Brand Dropdown

For `brand` field, add choices:

```
Money Machine
Solidarity
RAWSCROLL
On The Daily
YouTube_1
YouTube_2
YouTube_3
```

Default: `Money Machine`

### Step 2.4 — Auto-Fill Hidden Fields

Hide these columns (they auto-populate):
- `id`
- `status`
- `created_at`
- `script`
- `video_url`
- `posted_at`

Set defaults:
- `status` = `pending`
- `created_at` = `Now()`

### Step 2.5 — Lock the App

1. Glide → **Settings**
2. Privacy:
   - App visibility: **Private**
   - Access: **Only me**

### Step 2.6 — Install on Phone

📱 On your phone:
1. Open Glide app link in Chrome/Safari
2. Tap **Share** → **Add to Home Screen**
3. Rename icon: `ANOINTMENT`

✅ **PHONE CONTROLLER READY**

---

## PART 3 — CREATOMATE (25 min)

### Step 3.1 — Create Account

1. Go to [creatomate.com](https://creatomate.com)
2. Sign up
3. Dashboard → **API Keys**
4. Copy API key
5. Add to Railway environment variables:
   ```
   CREATOMATE_API_KEY=your_key_here
   ```

### Step 3.2 — Create Templates

#### 🎥 TEMPLATE 1: Original Content

**Name:** `original_vertical_template`

**Settings:**
- Format: 9:16
- Resolution: 1080x1920

**Elements:**
| Element | Variable Name |
|---------|---------------|
| Background video | `video_bg` |
| Text overlay | `script_text` |
| Music track | `music_url` |

**Save → Copy Template ID**

#### 🔥 TEMPLATE 2: Flood/Remix

**Name:** `flood_remix_template`

**Elements:**
| Element | Variable Name | Notes |
|---------|---------------|-------|
| Video source | `Video-Source` | X Scale: -100% (mirror) |
| Header text | `Brand-Header` | |
| Logo | `Brand-Logo` | Optional |

**Save → Copy Template ID**

### Step 3.3 — Add Template IDs to n8n

In your n8n workflows, update:
```
CREATOMATE_ORIGINAL_TEMPLATE=tmpl_xxxx
CREATOMATE_FLOOD_TEMPLATE=tmpl_yyyy
```

### Step 3.4 — Test Render

1. Use Creatomate's **Test Render** button
2. If it renders → you're done forever

✅ **RENDERING LAYER COMPLETE**

---

## PART 4 — VERIFY RAILWAY (5 min)

### Health Check

Open in browser:
```
https://YOUR-RAILWAY-APP.railway.app/health
```

Expected response:
```json
{
  "status": "operational",
  "ffmpeg_available": true,
  "timestamp": "2024-12-28T..."
}
```

✅ **REMIX ENGINE LIVE**

---

## PART 5 — FINAL TESTS

### Test 1: Original Content

1. Open **ANOINTMENT** app on phone
2. Fill form:
   - Brand: `Money Machine`
   - Topic: `New AI agents released today`
3. Submit
4. Open n8n → watch workflow execute
5. Confirm video posts to FB + IG

### Test 2: Flood Content

1. Manually trigger flood workflow in n8n
   - OR wait for next scheduled run (every 4h)
2. Confirm:
   - Video scraped from viral source
   - Remixed via Railway
   - Posted to RAWSCROLL + On The Daily

---

## 🎯 YOU ARE LIVE

### What You Can Now Do:
- ✅ Run everything from phone
- ✅ Post daily without thinking
- ✅ Flood repurposed content cheaply
- ✅ Scale without new tools
- ✅ Stay under $72/month

### What You Never Do Again:
- ❌ Build dashboards
- ❌ Touch VS Code for operations
- ❌ Rebuild Railway
- ❌ Manually edit videos
- ❌ Worry about watermark detection
- ❌ Debug blindly

---

## 🔒 FINAL STATUS

| Layer | Status |
|-------|--------|
| Google Sheets | ✅ |
| Glide Phone App | ✅ |
| Creatomate | ✅ |
| Railway Remix Engine | ✅ |
| n8n Workflows | ✅ |
| Apify Actors | ✅ |
| Suno Music | ✅ |

---

## 📱 QUICK REFERENCE CARD

**Daily Routine (2 min):**
1. Open ANOINTMENT app
2. Pick brand
3. Enter topic
4. Submit
5. Done

**Check Status:**
- n8n dashboard for workflow runs
- Error_Log sheet for issues
- Analytics sheet for metrics

**Emergency:**
- Check Error_Log in Google Sheets
- Healer response column has fix instructions

---

## 🚀 NEXT LEVELS (When Ready)

Say the word for:
- 💰 Monetization layer (affiliate, ads, products)
- 🧪 Auto A/B testing
- 📈 Scaling to client accounts
- 🏢 Turning this into SaaS

---

**You are operational.**  
**Not planning. Not configuring. Operating.**
