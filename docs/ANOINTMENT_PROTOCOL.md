# THE ANOINTMENT PROTOCOL
## Sovereign Architecture for Autonomous Media Systems (v1.0)

---

## 🔒 CORE DOCTRINE

> **The Hunter finds. The Brain decides. The Forge transforms.**
> **You profit.**

---

## 🧬 SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                    ANOINTMENT PROTOCOL                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  THE HUNTER (Apify)                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • TikTok Scraper → Rawscroll (velocity, volume)         │   │
│  │ • Instagram Scraper → OnTheDaily (authority, curation)  │   │
│  │ • Watermark Remover → Clean streams                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           ↓                                     │
│  THE BRAIN (n8n)                                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Viral filtering (Shares/Likes > 0.15)                 │   │
│  │ • Caption rewriting (Creative OS)                       │   │
│  │ • Routing to Forge + Distribution                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           ↓                                     │
│  THE FORGE (Railway)                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Fingerprint obfuscation (brightness, noise, desync)   │   │
│  │ • Metadata stripping                                    │   │
│  │ • H.264/AAC encoding                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           ↓                                     │
│  DISTRIBUTION (Graph API)                                      │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Instagram Reels (Container → Poll → Publish)          │   │
│  │ • Facebook Video (Parallel, not cross-post)             │   │
│  │ • First Comment injection (Money Machine)               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 FILE STRUCTURE

```
Money-Machine/
├── nixpacks.toml                    # Railway FFmpeg config
├── engines/
│   └── anointment_forge.py          # FastAPI backend
├── workflows/
│   └── n8n_anointment_protocol.json # Complete n8n workflow
└── data/apify/
    ├── rawscroll_tiktok_config.json
    ├── rawscroll_instagram_config.json
    ├── onthedaily_instagram_config.json
    └── watermark_remover_config.json
```

---

## 🔧 THE 422 ERROR FIX

The "422 Unprocessable Entity" error occurs from **double serialization**.

### ❌ WRONG (Double Serialization)
```javascript
// n8n HTTP Request Body
{
  "tags": "{{ JSON.stringify($json.hashtags) }}"
}
```
**Result:** Backend receives a STRING `"[\"#viral\", \"#money\"]"`

### ✅ CORRECT (Direct Expression)
```javascript
// n8n HTTP Request Body
{
  "tags": {{ $json.hashtags }}
}
```
**Result:** Backend receives an ARRAY `["#viral", "#money"]`

### Pydantic Schema (Railway)
```python
class ProcessingRequest(BaseModel):
    video_url: str
    tags: Optional[List[str]] = None  # Expects array, not string
    metadata: Optional[Dict[str, Any]] = None  # Expects object
```

---

## 🎯 THE ANOINTMENT (Fingerprint Obfuscation)

The Forge breaks both hash types to avoid shadowbans:

| Technique | Effect | Detection Method Defeated |
|-----------|--------|---------------------------|
| `brightness=0.01` | +1% brightness | MD5/SHA hash |
| `noise=alls=1` | Random noise | Perceptual hash (pHash) |
| `setpts=PTS/1.01` | 1% time desync | Temporal fingerprint |
| `-map_metadata -1` | Strip XMP tags | Platform metadata flags |
| `aecho=0.8:0.88:6:0.1` | Audio fingerprint | Audio hash |

### FFmpeg Command
```bash
ffmpeg -y -i input.mp4 \
  -vf "eq=brightness=0.01,noise=alls=1:allf=t+u,setpts=PTS/1.01" \
  -af "aecho=0.8:0.88:6:0.1" \
  -map_metadata -1 \
  -fflags +bitexact \
  -c:v libx264 -preset veryfast -crf 26 \
  -c:a aac -b:a 128k \
  output.mp4
```

---

## 📊 VIRAL TAXONOMY

### Rawscroll (Velocity + Volume)
- **Source:** Hashtags, trending sounds
- **Schedule:** Every 4 hours
- **Filter:** `Viral_Coefficient = Shares / Likes > 0.15`
- **Content:** Ephemeral, trend-based

### OnTheDaily (Authority + Consistency)
- **Source:** Specific creator profiles
- **Schedule:** Daily
- **Filter:** Top 50 posts, skip pinned, recency window
- **Content:** Gold standard, brand-aligned

---

## 🚀 DEPLOYMENT

### 1. Deploy Railway Backend
```bash
# In your Railway project
git push railway main
```

The `nixpacks.toml` automatically installs FFmpeg.

### 2. Import n8n Workflow
1. Open n8n
2. Import `workflows/n8n_anointment_protocol.json`
3. Set environment variables:
   - `APIFY_TOKEN`
   - `RAILWAY_BACKEND_URL`
   - `META_ACCESS_TOKEN`
   - `IG_USER_ID`
   - `FB_PAGE_ID`

### 3. Configure Apify Actors
Use the configs in `data/apify/` as templates.

---

## 💰 MONEY MACHINE INTEGRATION

### Affiliate Link Rotation
```javascript
// n8n Code Node
const offers = [
  "https://affiliate.com/offer1",
  "https://affiliate.com/offer2",
  "https://affiliate.com/offer3"
];
const selected = offers[$runIndex % offers.length];
const utm = `?utm_source=instagram&utm_campaign=anointment_${Date.now()}`;
return { link: selected + utm };
```

### First Comment Strategy
```javascript
// After media_publish succeeds
POST /{media-id}/comments
{
  "message": "🔥 Link in bio for the full breakdown! 👆"
}
```

---

## 🔒 CRITICAL RULES

1. **Never cross-post** - Use parallel native posting
2. **Never pass temp URLs directly** - Download to Railway first
3. **Never stringify arrays in n8n** - Use direct expressions
4. **Never skip watermark removal** - TikTok marks cause shadowbans
5. **Always wait for IG processing** - Poll status before publish

---

## 🏁 FINAL STATE

You now have:
- ✅ Autonomous content acquisition (Apify)
- ✅ Intelligent filtering (Viral Coefficient)
- ✅ Fingerprint obfuscation (Anointment)
- ✅ Parallel distribution (IG + FB)
- ✅ Revenue capture (First Comment + UTM)

**The system is sovereign. Execute.**
