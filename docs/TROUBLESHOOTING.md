# 🔧 Troubleshooting Guide

Common issues and solutions for the Money Machine.

---

## 🚨 Deployment Issues

### n8n Won't Start on Railway

**Symptoms:**
- Deployment fails
- Container keeps restarting
- Health check failing

**Solutions:**

1. **Check Environment Variables**
   ```
   N8N_ENCRYPTION_KEY=<must be at least 32 characters>
   N8N_HOST=0.0.0.0
   N8N_PORT=5678
   ```

2. **Check Memory Limits**
   - Railway free tier has limits
   - Upgrade if consistently hitting memory ceiling

3. **Check Database Connection**
   - Ensure PostgreSQL service is running
   - Check `DATABASE_URL` is auto-configured

4. **View Logs**
   - Railway Dashboard → Service → Deployments → View Logs

---

### "Cannot find module" Errors

**Cause:** Python engines not properly mounted

**Solution:**
1. Ensure engines directory exists: `/data/engines/`
2. Check Dockerfile copies files correctly
3. Verify with: `python3 -c "import sys; print(sys.path)"`

---

## 🎯 Hunter Engine Issues

### "Reddit Authentication Failed"

**Cause:** Invalid or expired credentials

**Solution:**
1. Verify credentials at [reddit.com/prefs/apps](https://reddit.com/prefs/apps)
2. Check you're using the correct Client ID (under app name)
3. Ensure User-Agent is set: `MoneyMachine/1.0`

### No Opportunities Found

**Causes:**
- Subreddits have low activity
- Rate limited
- API credentials not working

**Solution:**
1. Test with popular subreddits first
2. Check rate limit status in logs
3. Verify API credentials manually

---

## 🎨 Creator Engine Issues

### "TTS Generation Failed"

**Symptoms:**
- No audio file created
- Edge TTS errors

**Solutions:**

1. **Check Network**
   - Edge TTS requires internet access
   - Check Railway egress settings

2. **Test Manually**
   ```bash
   edge-tts --text "Hello World" --write-media /tmp/test.mp3
   ```

3. **Check Disk Space**
   - Ensure `/data/temp` has space

### "No Stock Footage Found"

**Cause:** Pexels API not configured or query too specific

**Solutions:**
1. Verify `PEXELS_API_KEY` is set
2. Try broader search terms
3. Check Pexels API status

### "FFmpeg Error"

**Symptoms:**
- Video assembly fails
- Codec errors

**Solutions:**

1. **Check Input Files**
   - Ensure audio file exists
   - Ensure background video exists

2. **Check FFmpeg Installation**
   ```bash
   ffmpeg -version
   ```

3. **Check Output Directory**
   - Ensure `/data/output` exists and is writable

---

## 📡 Gatherer Engine Issues

### "YouTube Upload Failed"

**Causes:**
- Quota exceeded (10,000 units/day)
- OAuth token expired
- Video rejected by YouTube

**Solutions:**

1. **Check Quota**
   - [YouTube API Dashboard](https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas)
   - Each upload = 1600 units
   - Max ~6 uploads per day

2. **Refresh Token**
   - In n8n, delete and recreate YouTube credential
   - Re-authorize with your account

3. **Check Video Requirements**
   - Must be < 128GB
   - Must be < 12 hours
   - Must have valid format

### "Rate Limit Exceeded"

**Cause:** Too many API calls

**Solution:**
- Survivor Engine handles this automatically
- Wait for reset (usually midnight UTC)
- Check daily limits in `GathererConfig`

### "Content ID Claim"

**Cause:** Copyrighted material detected

**Solution:**
- System auto-detects via `get_video_status()`
- Applies fingerprint modifications (pitch shift, color grade)
- Re-uploads automatically

---

## 💰 Businessman Engine Issues

### "Stripe Balance Returns 0"

**Causes:**
- API key not set
- Using test mode key
- No transactions yet

**Solutions:**
1. Verify `STRIPE_SECRET_KEY` is set
2. Ensure using live key (starts with `sk_live_`)
3. Check Stripe dashboard directly

### "Financial Snapshot Empty"

**Cause:** No API credentials configured

**Solution:**
- Configure at least one: Stripe, PayPal, or Mercury
- Test manually first

---

## 🛡️ Survivor Engine Issues

### "No Alerts Received"

**Causes:**
- Telegram bot not configured
- Wrong chat ID
- Bot not started

**Solutions:**

1. **Verify Bot Token**
   ```bash
   curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
   ```

2. **Verify Chat ID**
   - Message your bot first
   - Visit: `https://api.telegram.org/bot<TOKEN>/getUpdates`
   - Find your chat ID in response

3. **Start Bot**
   - Send `/start` to your bot in Telegram

### "Circuit Breaker Open"

**Cause:** Too many errors in short period (≥3 in 5 minutes)

**Solutions:**
1. Check error logs for root cause
2. Fix underlying issue
3. Reset circuit: `survivor.error_tracker.reset_circuit("component")`

### "Health Check Failing"

**Causes:**
- Service not responding
- Wrong endpoint
- Network issues

**Solutions:**
1. Check n8n is accessible: `curl http://localhost:5678/healthz`
2. Verify all dependent services (Postgres, Redis) are running

---

## 🔄 Workflow Issues

### "Workflow Not Executing"

**Causes:**
- Workflow not activated
- Trigger misconfigured
- Error in previous node

**Solutions:**
1. Check workflow is toggled **Active**
2. Check trigger settings (cron, webhook)
3. View execution history in n8n

### "Execute Command Node Fails"

**Causes:**
- Python not found
- Module not importable
- Syntax error in command

**Solutions:**

1. **Check Python Path**
   ```bash
   which python3
   python3 --version
   ```

2. **Check Module Import**
   ```bash
   cd /data && python3 -c "from engines.hunter import MasterHunter; print('OK')"
   ```

3. **Escape Quotes Properly**
   - Use single quotes inside double quotes
   - Or escape with backslash

### "Webhook Not Receiving"

**Causes:**
- Wrong URL
- Webhook not active
- Railway networking issue

**Solutions:**
1. Verify webhook URL matches Railway domain
2. Check workflow is active
3. Test with: `curl -X POST https://your-app.railway.app/webhook/create-content`

---

## 💾 Data Issues

### "Output Files Disappearing"

**Cause:** Railway uses ephemeral storage by default

**Solution:**
- Use Railway Volumes for persistent storage
- Or configure external storage (S3, etc.)

### "Database Connection Lost"

**Cause:** PostgreSQL service restarted or crashed

**Solutions:**
1. Check PostgreSQL service in Railway
2. Verify `DATABASE_URL` is still valid
3. Railway auto-reconnects, wait a moment

---

## 🔒 Security Issues

### "Credentials Exposed in Logs"

**Prevention:**
- Never log raw credentials
- Use environment variables
- Check n8n execution logs settings

### "Unauthorized API Access"

**Causes:**
- API key compromised
- Incorrect permissions

**Solutions:**
1. Rotate API keys immediately
2. Check API dashboard for suspicious activity
3. Update credentials in Railway

---

## 📊 Performance Issues

### "Slow Execution"

**Causes:**
- Large video files
- API rate limiting
- Insufficient resources

**Solutions:**
1. Optimize video settings (lower resolution for testing)
2. Implement caching
3. Upgrade Railway resources

### "Queue Backing Up"

**Cause:** More jobs than workers can handle

**Solutions:**
1. Add worker nodes (queue mode)
2. Reduce execution frequency
3. Increase worker resources

---

## 🆘 Emergency Procedures

### Complete System Failure

1. **Check Railway Status**: [status.railway.app](https://status.railway.app)
2. **Check All Services**: PostgreSQL, Redis, n8n
3. **Review Recent Changes**: What changed?
4. **Rollback if Needed**: Railway supports rollbacks
5. **Alert Owner**: Telegram/Discord notification

### Revenue Stream Down

1. **Check Affected Platform**: YouTube, TikTok, etc.
2. **Verify API Access**: Token expired?
3. **Check Account Status**: Shadowban? Suspension?
4. **Switch to Backup**: Redistribute to other platforms
5. **Document and Fix**: For future prevention

---

## 📞 Getting Help

1. **Check Logs First**: 80% of issues are in the logs
2. **Search GitHub Issues**: Someone may have solved it
3. **n8n Community**: [community.n8n.io](https://community.n8n.io)
4. **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)

---

**Remember: The Survivor Engine is designed to handle most issues automatically. Check its logs and alerts first!**
