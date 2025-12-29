# Money Machine n8n Workflow - Complete Setup Guide

## 🎯 What This Workflow Does

This n8n workflow automates your entire video production pipeline:

1. **Triggers** (3 ways to start):
   - ⏰ **Scheduled**: Every 30 minutes automatically selects an elite topic
   - 🖱️ **Manual**: Click to run with random elite topic
   - 📝 **Form**: Web form at `/money-machine-form` for custom topics

2. **Script Generation**: GPT-4o writes viral scripts with 12-15 beats

3. **Visual Grounding**: Converts abstract intents to concrete visual prompts

4. **Multi-Provider Generation**: Routes scenes to 7 different AI providers:
   - Leonardo AI (anime_dark style)
   - Runway ML (cinematic_real style)  
   - Fal.ai (abstract_metaphor style)
   - Replicate (glitch_data style)
   - Kie AI (motion_cinematic style)
   - Stability AI (hyperreal style)
   - Shotstack (documentary style)

5. **Audio**: ElevenLabs TTS with Adam voice

6. **Assembly**: Shotstack cloud rendering with audio sync

7. **Upload**: Direct to YouTube (Money Machine AI channel)

8. **Analysis**: Claude analyzes DNA for next video mutations

9. **Logging**: Airtable stores evolution history

10. **Notifications**: Telegram alerts on success/failure

---

## 🔑 Credentials Already Embedded

All your credentials from `.env` are already in the workflow:

| Service | API Key Used |
|---------|-------------|
| OpenAI GPT-4o | `sk-proj-ifc7RtNBJfBX7U1Y3D5P...` |
| Anthropic Claude | `sk-ant-api03-7NTyQKigOQ...` |
| ElevenLabs | `sk_5d8bfc9c41d35a9a8a47516...` |
| Leonardo AI | `8a7ccd1c-6aa6-4a0e-a28e-4d461b542212` |
| Runway ML | `key_d327367da695c4e0b7005c...` |
| Fal.ai | `04cc9251-3b11-482a-b89d-980f7a6791e4:1db3d89f...` |
| Replicate | `r8_KiMLmUgX42aR8BvP711dPrVdTfYn8Oj2UVVbX` |
| Kie AI | `b2d832f78ac1d0e818aacc02c11aca48` |
| Stability AI | `sk-nKoQVkvdM7w1cYfiTp1wSxGowNG3F9wk...` |
| Shotstack | `sofi4GJNxp6XncLw3t46Cqe4n73lDAd09wrd3JIV` |
| Airtable | `patrb7eUEX1MrJJY0.f98139302c5bdeb...` |
| Telegram Chat ID | `5033650061` |

---

## ⚙️ Setup Steps in n8n

### 1. Import the Workflow

1. Open n8n (locally or Railway deployment)
2. Go to **Workflows** → **Import from File**
3. Select: `workflows/n8n_money_machine_complete.json`
4. Click **Import**

### 2. Configure YouTube OAuth Credentials

The YouTube Upload node needs OAuth2 credentials. Create them in n8n:

1. Go to **Credentials** → **Add Credential** → **YouTube OAuth2 API**
2. Name it: `YouTube Money Machine AI`
3. Fill in these values from your `.env`:

```
Client ID: 1028076833530-g8mfugtt3j4cna45c14mukqgmup6aelh.apps.googleusercontent.com
Client Secret: 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
```

4. Click **Connect** and authorize with your `bullygang0086@gmail.com` account
5. The credential will store the refresh token automatically

### 3. Configure Telegram Credentials

1. Go to **Credentials** → **Add Credential** → **Telegram API**
2. Name it: `Money Machine Bot`
3. Fill in:

```
Bot Token: 8501373839:AAGQley_8ZKwhzMzU7HTooonBb1ufiYj-Gw
```

4. Save

### 4. Create Airtable Base (One-Time)

1. Go to [Airtable](https://airtable.com)
2. Create a new base called `MoneyMachineDNA`
3. Create a table called `DNA_Log` with these fields:
   - `Timestamp` (Date/Time)
   - `Video_ID` (Single line text)
   - `Title` (Single line text)
   - `Thesis` (Long text)
   - `Scene_Count` (Number)
   - `Providers` (Single line text)
   - `Styles` (Single line text)
   - `AAVE_Mutations` (Long text)
4. Get the base ID from the URL (starts with `app...`)
5. Update the Airtable node URL to use your base ID

---

## 🔧 What I Fixed/Changed

### API Endpoints (Critical Fixes)

| Provider | Old (Broken) | New (Working) |
|----------|-------------|---------------|
| Runway ML | `api.runwayml.com/v1/image_to_video` | `api.dev.runwayml.com/v1/text_to_image` |
| Runway Model | `gen3a_turbo` | `gen4_image` |
| Kie AI | `api.kieai.app/v1/generations` | `api.kie.ai/api/v1/flux/kontext/generate` |
| Leonardo AI | Not included | Added with Kino XL model |

### Visual Grounding Added

The Scene Planner now includes a `VISUAL_MAP` that converts abstract intents to concrete objects:

```javascript
'debt' → 'credit card statement closeup, negative balance on screen'
'banks' → 'bank vault door, gold bars stacked, marble columns'
'control' → 'puppet strings on hands, surveillance camera eye'
```

### Quality Gate Enforcement

- Minimum 10 scenes required
- Minimum 3 providers required
- No consecutive duplicate styles
- Automatic style rotation on conflict

### Added Features

1. **Scheduled Trigger**: Runs every 30 minutes
2. **Elite Topic Selector**: 10 pre-loaded viral topics
3. **Error Handling**: Stops pipeline and alerts on failure
4. **Leonardo AI Provider**: Added as 7th provider
5. **Shotstack Fallback**: Added for documentary style

---

## 📍 File Locations

The workflow expects these directories (create if needed):

```
/data/audio/       - Voice files from ElevenLabs
/data/scenes/      - Individual scene videos
/data/output/      - Final rendered videos
```

For Railway/Docker deployment, these map to your container's filesystem.

---

## 🚀 Running the Workflow

### Manual Test
1. Click on "Manual Trigger" node
2. Click "Execute Node"
3. Watch the execution flow through all nodes

### Scheduled Production
1. Activate the workflow (toggle in top right)
2. The "Every 30 Minutes" trigger will fire automatically
3. Check Telegram for notifications

### Custom Topic via Form
1. Go to: `https://your-n8n-url.com/webhook/money-machine-form`
2. Enter your topic, style, and duration
3. Submit and watch the magic

---

## 🔐 Security Note

⚠️ **This workflow contains your real API keys!** 

- Never share the JSON file publicly
- The file is already in `.gitignore`
- Consider using n8n's credential system instead of hardcoded values

To migrate to n8n credentials:
1. Create credentials for each service
2. Replace hardcoded `Authorization` headers with credential references
3. Use `{{ $credentials.serviceName.apiKey }}` syntax

---

## 📊 Expected Costs Per Video

| Service | Est. Cost |
|---------|-----------|
| GPT-4o | ~$0.02 |
| ElevenLabs | ~$0.10 |
| Visual Providers (avg) | ~$0.50 |
| Shotstack Render | ~$0.25 |
| **Total** | **~$0.87/video** |

At 48 videos/day (every 30 min): ~$42/day

---

## 🛠️ Troubleshooting

### "Rate limit exceeded"
- Add delays between provider calls
- Reduce scheduled frequency to every 60 min

### "YouTube upload failed"
- Re-authorize OAuth credentials
- Check channel quota (10,000 units/day)

### "Shotstack render timeout"
- Increase wait time before download
- Reduce scene count to 10

### "Provider X failed"
- Check API key validity
- Check account balance/credits
- The merge node will continue with successful providers

---

## 📁 File Location

```
workflows/n8n_money_machine_complete.json
```

Import this directly into n8n!
