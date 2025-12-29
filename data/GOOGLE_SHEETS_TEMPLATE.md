# ANOINTMENT SYSTEM - GOOGLE SHEETS TEMPLATE
## Import this structure into your Google Sheet

---

## Sheet 1: Queue (Content Queue)
| Column | Type | Description |
|--------|------|-------------|
| id | Auto | Row ID |
| topic | Text | Content topic |
| brand | Dropdown | money_machine, solidarity, youtube_1, youtube_2, youtube_3 |
| tone | Text | cinematic dark, upbeat, motivational |
| status | Dropdown | pending, processing, published, failed |
| created_at | DateTime | When added |
| published_at | DateTime | When published |
| video_url | URL | Final video URL |
| notes | Text | Optional notes |

**Sample Data:**
```
id | topic | brand | tone | status | created_at
1 | Why the Rich Use Debt | money_machine | cinematic dark | pending | 2025-12-28
2 | Morning Routine Secrets | solidarity | upbeat | pending | 2025-12-28
3 | AI Tools for 2025 | youtube_1 | motivational | pending | 2025-12-28
```

---

## Sheet 2: Error_Log (Error Tracking)
| Column | Type | Description |
|--------|------|-------------|
| timestamp | DateTime | When error occurred |
| workflow | Text | Which workflow failed |
| node | Text | Which node failed |
| error | Text | Error message |
| diagnosis | Text | Auto-Healer diagnosis |
| fix | Text | Fix instructions |
| status | Dropdown | pending_fix, fixed, ignored |

---

## Sheet 3: Brands (Brand Configuration)
| Column | Type | Description |
|--------|------|-------------|
| brand_id | Text | Unique identifier |
| display_name | Text | Human-readable name |
| ig_user_id | Text | Instagram User ID |
| fb_page_id | Text | Facebook Page ID |
| meta_token | Text | Meta API Token |
| youtube_channel | Text | YouTube Channel ID |
| hashtags | Text | Default hashtags |
| tone | Text | Default tone |

**Sample Data:**
```
brand_id | display_name | ig_user_id | fb_page_id | hashtags
money_machine | Money Machine AI | 123456789 | 987654321 | #MoneyMachine #AI #Wealth
solidarity | Solidarity Ointments | 234567890 | 876543210 | #Solidarity #Wellness
youtube_1 | Tech Channel | - | - | #Tech #AI #Future
rawscroll | RAWSCROLL | 345678901 | 765432109 | #viral #trending #fyp
onthedaily | On The Daily | 456789012 | 654321098 | #onthedaily #motivation
```

---

## Sheet 4: Music_Bank (Suno Track References)
| Column | Type | Description |
|--------|------|-------------|
| track_id | Text | Suno track ID |
| name | Text | Track name |
| mood | Dropdown | Dark, Phonk, Tech, Upbeat, Cinematic |
| duration | Number | Seconds |
| drive_url | URL | Google Drive link |
| usage_count | Number | Times used |

---

## Sheet 5: Analytics (Performance Tracking)
| Column | Type | Description |
|--------|------|-------------|
| date | Date | Date |
| brand | Text | Which brand |
| platform | Text | IG, FB, TikTok, YouTube |
| posts | Number | Posts that day |
| views | Number | Total views |
| engagement | Number | Likes + comments |
| cost | Currency | Cost that day |
| revenue | Currency | Revenue that day |

---

## Sheet 6: Flood_Log (Repurposing Tracking)
| Column | Type | Description |
|--------|------|-------------|
| timestamp | DateTime | When posted |
| source_url | URL | Original viral content |
| source_platform | Text | TikTok, IG, FB |
| source_views | Number | Original view count |
| remixed_url | URL | Anointed version |
| posted_to | Text | Platforms posted |
| cost | Currency | Processing cost |

---

## GLIDE APP CONFIGURATION

### Screens:
1. **Queue Manager** - Add new content requests
2. **Brand Selector** - Dropdown for brand selection
3. **Error Dashboard** - View and manage errors
4. **Analytics** - View performance

### Forms:
**New Content Form:**
- Topic (text input)
- Brand (dropdown from Brands sheet)
- Tone (dropdown: cinematic dark, upbeat, motivational)
- Submit → Adds row to Queue with status=pending

### Data Sources:
- All sheets connected to Glide
- Real-time sync enabled

---

## n8n ENVIRONMENT VARIABLES NEEDED

```
# Google Sheets
GOOGLE_SHEET_ID=your_sheet_id_here

# Apify
APIFY_TOKEN=your_apify_token

# Suno Music Bank
SUNO_MUSIC_FOLDER_ID=your_google_drive_folder_id

# Creatomate
CREATOMATE_API_KEY=your_creatomate_key
CREATOMATE_TEMPLATE_ID=your_template_id

# Money Machine Brand
MM_IG_USER_ID=instagram_user_id
MM_FB_PAGE_ID=facebook_page_id
MM_META_TOKEN=meta_access_token

# Solidarity Brand
SOLIDARITY_IG_USER_ID=instagram_user_id
SOLIDARITY_FB_PAGE_ID=facebook_page_id
SOLIDARITY_META_TOKEN=meta_access_token

# RAWSCROLL Brand
RAWSCROLL_IG_USER_ID=instagram_user_id
RAWSCROLL_FB_PAGE_ID=facebook_page_id
RAWSCROLL_META_TOKEN=meta_access_token

# OnTheDaily Brand
ONTHEDAILY_IG_USER_ID=instagram_user_id
ONTHEDAILY_FB_PAGE_ID=facebook_page_id
ONTHEDAILY_META_TOKEN=meta_access_token

# Railway Backend
RAILWAY_BACKEND_URL=https://your-railway-app.up.railway.app

# Notifications
TELEGRAM_CHAT_ID=your_telegram_chat_id
ADMIN_EMAIL=your@email.com
```
