# Deployment Guide: Deploy on Streamlit Cloud

**Updated**: 2026-01-24

---

## Deploy in 5 Minutes with Streamlit Cloud

Streamlit Cloud is the **recommended** and **easiest** way to deploy Conscious Cart Coach.

---

## Why Streamlit Cloud?

**Perfect for Streamlit apps**:
- ✅ Built specifically for Streamlit (no configuration needed)
- ✅ Free tier available (unlimited public apps)
- ✅ One-click deployment from GitHub
- ✅ Automatic HTTPS
- ✅ Built-in secrets management
- ✅ Auto-deploys on git push
- ✅ Custom domains supported
- ✅ Zero maintenance

**Cost**:
- Free for public repos
- $20/month for private repos

---

## Step-by-Step Deployment

### 1. Prerequisites

✅ Code in GitHub repository
✅ GitHub account
✅ Anthropic API key (for AI features)
✅ Opik API key (optional, for monitoring)

### 2. Prepare Your Repository

```bash
# Make sure your code is pushed to GitHub
cd /Users/snair/Documents/projects/ConsciousBuyer
git add .
git commit -m "Ready for Streamlit Cloud deployment"
git push origin main
```

### 3. Sign Up for Streamlit Cloud

1. Go to **https://share.streamlit.io**
2. Click **"Sign in with GitHub"**
3. Authorize Streamlit to access your repositories

### 4. Deploy Your App

1. Click **"New app"** button
2. Fill in deployment settings:
   - **Repository**: `ConsciousBuyer` (or your repo name)
   - **Branch**: `main`
   - **Main file path**: `conscious-cart-coach/src/ui/app.py`
3. Click **"Deploy!"**

**That's it!** Streamlit will build and deploy your app.

Your app will be live at: `https://consciousbuyer.streamlit.app`

**Build time**: ~2-3 minutes

### 5. Configure Secrets

Once deployed, add your API keys:

1. Click **Settings** → **Secrets**
2. Add the following in TOML format:

```toml
# Required for AI features
ANTHROPIC_API_KEY = "sk-ant-api03-your_actual_key_here"

# Optional: Opik monitoring
OPIK_API_KEY = "your_opik_api_key"
OPIK_WORKSPACE = "chat"
OPIK_PROJECT_NAME = "consciousbuyer"
```

3. Click **"Save"**
4. App will automatically restart with new secrets

### 6. Verify Deployment

1. Open your app URL: `https://consciousbuyer.streamlit.app`
2. Test AI features:
   - Go to ⚙️ Preferences
   - Enable "AI ingredient extraction"
   - Create a cart with natural language prompt
3. Check Opik dashboard to verify tracking works

**Total deployment time**: 5 minutes ⏱️

### 7. Custom Domain (Optional)

Want to use your own domain?

1. Purchase domain (e.g., `consciousbuyer.com`)
2. In Streamlit Cloud dashboard:
   - Go to **Settings** → **Custom domains**
   - Click **"Add domain"**
   - Enter your domain
3. Update DNS records with your domain registrar:
   - Add CNAME record pointing to your Streamlit app
4. Wait for DNS propagation (~5-60 minutes)
5. Done! Access app at your custom domain

---

## Auto-Deploy on Git Push

Streamlit Cloud automatically redeploys when you push to GitHub:

```bash
# Make changes to your code
git add .
git commit -m "Update feature"
git push origin main

# Streamlit Cloud detects push and redeploys automatically
# App updates in ~2-3 minutes
```

No manual deployment needed!

---

## Alternative Deployment Platforms

While Streamlit Cloud is recommended, here are alternatives if you need them:

### Other Options

| Platform | Best For | Cost | Setup Time |
|----------|----------|------|------------|
| **Render** | PostgreSQL needs | Free tier, then $7/month | 10 min |
| **Railway** | Developer experience | $5/month | 5 min |
| **Heroku** | Legacy compatibility | From $7/month | 15 min |
| **Docker + Cloud** | Enterprise/custom | Varies | 30 min |

### Quick Links

- **Render**: https://render.com (good for PostgreSQL database)
- **Railway**: https://railway.app (great DX, simple CLI)
- **Google Cloud Run**: Use Docker + serverless
- **AWS ECS/Fargate**: Enterprise-grade container hosting

### Why NOT Vercel?

❌ Vercel is **not compatible** with Streamlit:
- Serverless functions have 10-second timeout
- No WebSocket support (required by Streamlit)
- Designed for Next.js/static sites, not long-running Python apps

**Recommendation**: Stick with Streamlit Cloud for the best experience.

## Pre-Deployment Checklist

Before deploying, make sure:

### 1. Requirements File is Complete

```bash
# Check requirements.txt
cat conscious-cart-coach/requirements.txt
```

Should include:
```txt
streamlit>=1.30.0
anthropic>=0.18.0
opik>=0.1.0
pandas>=2.0.0
sqlalchemy>=2.0.0
python-dotenv>=1.0.0
```

### 2. Environment Variables Ready

Create `.env.production` (don't commit!):
```bash
ANTHROPIC_API_KEY=sk-ant-api03-your_production_key
OPIK_API_KEY=your_production_key
OPIK_WORKSPACE=production
OPIK_PROJECT_NAME=consciousbuyer
```

### 3. Database Path Updated

In production, update SQLite path:
```python
# src/data/database.py
DATABASE_PATH = os.getenv("DATABASE_PATH", "/data/conscious_cart.db")
```

### 4. Remove Debug Code

```python
# Remove any debug prints, test data, or development-only features
# Check for:
# - print() statements
# - logger.debug() in production
# - Test API keys hardcoded
```

### 5. Test Locally First

```bash
# Run production-like environment locally
export ANTHROPIC_API_KEY=your_key
streamlit run conscious-cart-coach/src/ui/app.py --server.port 8501
```

Open http://localhost:8501 and test:
- ✅ LLM extraction works
- ✅ Cart creation works
- ✅ No errors in console
- ✅ Opik tracking works

---

## Post-Deployment Setup

### 1. Monitor Opik Dashboard

After first deployment:
1. Go to Opik dashboard
2. Verify traces are coming in
3. Set up cost alerts:
   - Daily limit: $5
   - Monthly limit: $50

### 2. Set Up Error Monitoring (Optional)

**Sentry for Streamlit**:
```python
# Add to app.py
import sentry_sdk

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0,
)
```

### 3. Add Analytics (Optional)

**Google Analytics for Streamlit**:
```python
# Add to app.py
import streamlit.components.v1 as components

components.html("""
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
""", height=0)
```

### 4. Set Up Backups

**SQLite Database Backup**:
```bash
# Create daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
sqlite3 /data/conscious_cart.db ".backup /backups/conscious_cart_$DATE.db"
```

---

## Recommended Deployment: Streamlit Cloud

For Conscious Cart Coach, **Streamlit Cloud is the best choice** because:

1. **Zero configuration** - works out of the box
2. **Free for public repos** - no cost
3. **Built for Streamlit** - no compatibility issues
4. **Auto-deploys** - git push → live
5. **Secrets management** - built-in
6. **Custom domains** - supported
7. **HTTPS** - automatic

### Quick Start (5 Minutes)

```bash
# 1. Push to GitHub
git push origin main

# 2. Go to https://share.streamlit.io
# 3. Click "New app"
# 4. Select: ConsciousBuyer/main/conscious-cart-coach/src/ui/app.py
# 5. Add secrets in dashboard
# 6. Click "Deploy"

# Done! Live at: https://consciousbuyer.streamlit.app
```

---

## Troubleshooting Deployment

### Issue: "ModuleNotFoundError"

**Cause**: Missing dependency in requirements.txt

**Fix**:
```bash
# Add missing package
echo "missing-package>=1.0.0" >> requirements.txt
git commit -am "Add missing dependency"
git push
```

### Issue: "Application Error"

**Cause**: Environment variable not set

**Fix**:
1. Check deployment platform's environment variables
2. Verify ANTHROPIC_API_KEY is set
3. Check logs for specific error

### Issue: "Port already in use"

**Cause**: Streamlit port conflict

**Fix**:
```bash
# Use different port
streamlit run app.py --server.port 8502
```

### Issue: "Database locked"

**Cause**: SQLite not suitable for multi-user production

**Fix**:
1. Use PostgreSQL for production
2. Update `src/data/database.py`:
```python
# Use PostgreSQL in production
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///conscious_cart.db")
engine = create_engine(DATABASE_URL)
```

---

## Cost Estimates

### Streamlit Cloud (Recommended)
- **Free tier**: Public repos, unlimited apps
- **Paid**: $20/month for private repos

### Render
- **Free tier**: 750 hours/month (enough for 24/7)
- **Paid**: $7/month for better performance

### Railway
- **Free tier**: $5 credit/month (~200 hours)
- **Paid**: Pay-as-you-go, ~$5-10/month

### API Costs (All Platforms)
- **Anthropic Claude**: ~$0.045 per cart with LLM features
- **Expected usage**: 100 carts/month = $4.50/month
- **Opik tracking**: Free tier (up to 100k traces/month)

**Total monthly cost**: $0-25/month depending on platform

---

## Security Checklist

Before going live:

- [ ] Remove all hardcoded API keys
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS (auto on most platforms)
- [ ] Set up rate limiting (Streamlit has built-in)
- [ ] Add authentication if needed (Streamlit Auth component)
- [ ] Review Opik data privacy (no PII in traces)
- [ ] Set up cost alerts on Anthropic dashboard
- [ ] Regular dependency updates (`pip list --outdated`)

---

## Next Steps After Deployment

1. **Share your app**:
   ```
   https://consciousbuyer.streamlit.app
   ```

2. **Monitor usage**:
   - Streamlit Cloud analytics (built-in)
   - Opik dashboard (LLM costs and performance)
   - Anthropic API usage dashboard

3. **Gather feedback**:
   - Add feedback form in UI
   - Monitor error rates
   - Track which features users use most

4. **Iterate**:
   - Fix bugs reported by users
   - Add requested features
   - Optimize based on Opik data

---

## Related Documentation

- [Architecture Overview](0-step.md)
- [LLM Integration](6-llm-integration-deep-dive.md)
- [Opik Monitoring](9-opik-llm-evaluation.md)
- [Testing Guide](../conscious-cart-coach/tests/README.md)

---

**Last updated**: 2026-01-24
**Recommended platform**: Streamlit Cloud
**Deployment time**: 5 minutes
**Monthly cost**: $0-25 depending on platform
**Difficulty**: ⭐ Easy (Streamlit Cloud) to ⭐⭐⭐ Advanced (Docker)
