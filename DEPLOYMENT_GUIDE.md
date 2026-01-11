# Streamlit Deployment Guide

## 🎯 Step-by-Step Deployment to Streamlit Cloud (Free)

### Step 1: Prepare Your Code

**Make sure everything works locally:**

```bash
# Test locally first
uv run python run_streamlit.py
```

**Verify:**
- ✅ App opens at http://localhost:8501
- ✅ Agent initializes successfully
- ✅ Questions get answered

---

### Step 2: Push to GitHub

**Create a GitHub repository:**
1. Go to https://github.com/new
2. Create a new repository (e.g., `doc-qa-agent`)
3. Choose **Private** or **Public**
4. Click "Create repository"

**Push your code:**

```bash
# Initialize git (if not already)
git init

# Add all files
git add .

# Commit
git commit -m "Initial commit: Complete Documentation Q&A Agent"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/your-username/doc-qa-agent.git

# Push
git push -u origin main
```

**Important:** Make sure to add `.env` to `.gitignore` (it's already there)

---

### Step 3: Set Up Streamlit Cloud

**Go to Streamlit Cloud:**
- https://streamlit.io/cloud

**Sign in:**
- Use your GitHub account
- Authorize Streamlit

---

### Step 4: Create New App

1. **Click "New app"** (top right)
2. **Select your repository** from the list
3. **Choose branch:** `main`
4. **Set main file path:** `app/streamlit_app.py`

---

### Step 5: Add API Key as Secret

1. **In the app settings**, go to "Secrets"
2. **Add a new secret:**
   - Name: `OPENROUTER_API_KEY`
   - Value: `sk-or-v1-your-actual-key-here`
3. **Save**

**Alternative:** Add to `.streamlit/secrets.toml`:

```bash
# Create secrets directory
mkdir -p .streamlit

# Create secrets file
echo "OPENROUTER_API_KEY='sk-or-v1-your-key-here'" > .streamlit/secrets.toml

# Add to git
git add .streamlit/secrets.toml
git commit -m "Add Streamlit secrets"
git push
```

---

### Step 6: Deploy!

1. **Click "Deploy"**
2. **Wait for build** (takes 2-5 minutes)
3. **App will open automatically** when ready

---

## 📋 Deployment Checklist

- [ ] Code works locally
- [ ] Pushed to GitHub
- [ ] Repository is public (or private with access)
- [ ] API key added as secret
- [ ] Main file set to `app/streamlit_app.py`
- [ ] Branch set to `main`

---

## ⚠️ Important Notes

### First Deployment is Slow
- **Build time:** 2-5 minutes
- **Reason:** Installs all dependencies
- **Subsequent deploys:** Faster (1-2 minutes)

### Free Tier Limitations
- **Memory:** 1GB RAM
- **CPU:** Shared
- **Storage:** 1GB
- **Timeout:** 30 minutes of inactivity
- **Bandwidth:** Limited

### Cost
- **Free tier:** Available
- **Paid plans:** Start at $25/month for more resources

---

## 🔧 Advanced Deployment Options

### Option 1: Using requirements.txt

Streamlit Cloud prefers `requirements.txt`. Let's create one:

```bash
# Generate requirements.txt from pyproject.toml
uv pip freeze > requirements.txt

# Add to git
git add requirements.txt
git commit -m "Add requirements.txt for Streamlit Cloud"
git push
```

### Option 2: Custom Domain

1. Go to app settings
2. Click "Domain"
3. Add your custom domain
4. Configure DNS

### Option 3: Environment Variables

Add to `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#FF4B4B"
backgroundColor = "#FFFFFF"
```

---

## 🌐 Alternative Deployment Platforms

### Heroku

1. **Create `Procfile`:**
   ```
   web: streamlit run app/streamlit_app.py --server.port=$PORT
   ```

2. **Create `runtime.txt`:**
   ```
   python-3.12.0
   ```

3. **Deploy:**
   ```bash
   heroku create
   git push heroku main
   heroku config:set OPENROUTER_API_KEY=your-key
   ```

### Railway

1. **Create new project**
2. **Connect GitHub repo**
3. **Set environment variable:** `OPENROUTER_API_KEY`
4. **Deploy**

### Google Cloud Run

1. **Create Dockerfile:**
   ```dockerfile
   FROM python:3.12
   
   WORKDIR /app
   COPY . .
   
   RUN uv sync
   
   CMD ["streamlit", "run", "app/streamlit_app.py", "--server.port=8080"]
   ```

2. **Build and deploy:**
   ```bash
   gcloud builds submit --tag gcr.io/your-project/doc-qa-agent
   gcloud run deploy --image gcr.io/your-project/doc-qa-agent --platform managed
   ```

---

## 🚀 Post-Deployment Tips

### Monitor Performance
- Check Streamlit Cloud dashboard
- Monitor memory usage
- Watch for timeouts

### Update Regularly
```bash
# Make changes
git add .
git commit -m "Update app"
git push
```

### Share Your App
- Share the URL
- Add to portfolio
- Get feedback

---

## 📚 Troubleshooting Deployment

### "App failed to build"

**Check:**
- `requirements.txt` exists
- All dependencies listed
- No syntax errors

### "Module not found"

**Fix:**
```bash
# Reinstall dependencies
uv sync

# Regenerate requirements.txt
uv pip freeze > requirements.txt

# Push changes
git add requirements.txt
git commit -m "Update requirements"
git push
```

### "API key not found"

**Fix:**
- Check secret is added correctly
- Verify secret name: `OPENROUTER_API_KEY`
- Test locally first

### "App times out"

**Fix:**
- Reduce initialization time
- Use smaller repository
- Upgrade to paid plan

---

## 🎉 Success!

Your app is now live at:
```
https://your-app-name.streamlit.app
```

Share it with the world! 🌍

---

**Need more help?**
- Check Streamlit Cloud docs: https://docs.streamlit.io/streamlit-cloud
- Join Streamlit community: https://discuss.streamlit.io/
- Ask questions: https://github.com/streamlit/streamlit/issues
