# Deploy to Streamlit Cloud in 5 Minutes

**Quick deployment guide for Conscious Cart Coach**

---

## Prerequisites

- ✅ Code pushed to GitHub
- ✅ GitHub account
- ✅ Anthropic API key (optional, for AI features)

---

## Steps

### 1. Sign Up

Go to **https://share.streamlit.io** and sign in with GitHub.

### 2. Deploy

1. Click **"New app"**
2. Select:
   - **Repository**: `ConsciousBuyer`
   - **Branch**: `main`
   - **Main file**: `conscious-cart-coach/src/ui/app.py`
3. Click **"Deploy!"**

### 3. Add Secrets

After deployment, go to **Settings → Secrets** and add:

```toml
# Required for AI features
ANTHROPIC_API_KEY = "sk-ant-api03-your_key_here"

# Optional for monitoring
OPIK_API_KEY = "your_opik_key"
OPIK_WORKSPACE = "chat"
OPIK_PROJECT_NAME = "consciousbuyer"
```

Click **Save**.

---

## Done! 🎉

Your app is live at: `https://consciousbuyer.streamlit.app`

Auto-deploys on every git push to `main` branch.

---

## Cost

- **Free** for public GitHub repos
- $20/month for private repos

---

## Need More Details?

See **[Full Deployment Guide](architecture/10-deployment-guide.md)** for:
- Custom domains
- Troubleshooting
- Alternative platforms
- Advanced configuration

---

**Deployment time**: 5 minutes ⏱️ | **Difficulty**: ⭐ Easy
