# Deployment Guide - Free Alternatives

## 🎯 Recommended: Render + Vercel (100% Free)

**Best free setup:**
- **Frontend**: Vercel (free, excellent performance)
- **Backend**: Render free tier
- **Agent**: Render free tier

**Total Cost: $0/month** (services sleep after 15 min on free tier)

---

## Option 1: Render (Free Tier) ⭐

### Deploy Backend on Render

1. Go to [render.com](https://render.com) and sign up with GitHub (free)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure:
   - **Name**: `restaurant-booking-backend`
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Node`
   - **Build Command**: `npm install`
   - **Start Command**: `npm start`
   - **Plan**: **Free** (or Starter $7/month for always-on)

5. Add Environment Variables:
   ```
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/restaurant-bookings
   OPENWEATHER_API_KEY=your_openweathermap_api_key
   RESTAURANT_LOCATION=Mumbai
   RESTAURANT_EMAIL=restaurant@example.com
   EMAIL_USER=your_email@gmail.com
   EMAIL_PASS=your_app_password
   LIVEKIT_API_KEY=your_livekit_api_key
   LIVEKIT_API_SECRET=your_livekit_api_secret
   PORT=5000
   NODE_ENV=production
   ALLOWED_ORIGINS=https://your-frontend-url.vercel.app,http://localhost:3000
   ```

6. Click **"Create Web Service"**
7. Render will generate URL: `https://restaurant-booking-backend.onrender.com`
   - ⚠️ **Note**: Free tier services sleep after 15 min inactivity (first request may be slow)

### Deploy Agent on Render

1. In Render dashboard, click **"New +"** → **"Background Worker"**
2. Connect the same GitHub repository
3. Configure:
   - **Name**: `restaurant-booking-agent`
   - **Region**: Same as backend
   - **Branch**: `main`
   - **Root Directory**: `agent`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python agent.py dev`
   - **Plan**: **Free** (or Starter $7/month for always-on)

4. Add Environment Variables:
   ```
   LIVEKIT_URL=wss://your-project.livekit.cloud
   LIVEKIT_API_KEY=your_livekit_api_key
   LIVEKIT_API_SECRET=your_livekit_api_secret
   OPENAI_API_KEY=your_openai_api_key
   BACKEND_URL=https://restaurant-booking-backend.onrender.com
   ```

5. Click **"Create Background Worker"**

### Deploy Frontend on Vercel (Recommended)

1. Go to [vercel.com](https://vercel.com) and sign up with GitHub (free)
2. Click **"Add New"** → **"Project"**
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
   - **Install Command**: `npm install`

5. Add Environment Variables:
   ```
   REACT_APP_LIVEKIT_URL=wss://your-project.livekit.cloud
   REACT_APP_BACKEND_URL=https://restaurant-booking-backend.onrender.com
   ```

6. Click **"Deploy"**
7. Vercel will generate URL: `https://restaurant-booking.vercel.app`

---

## Option 2: Fly.io (Always-On Free Tier) 🚀

Fly.io offers 3 free shared VMs that **don't sleep** - perfect for always-on services!

### Setup Fly.io CLI

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login
```

### Deploy Backend

```bash
cd backend

# Initialize Fly app
fly launch

# Configure (when prompted):
# - App name: restaurant-booking-backend
# - Region: Choose closest (e.g., iad, ord, dfw)
# - PostgreSQL: No
# - Redis: No

# Set environment variables
fly secrets set MONGODB_URI="mongodb+srv://..." \
  OPENWEATHER_API_KEY="..." \
  RESTAURANT_LOCATION="Mumbai" \
  RESTAURANT_EMAIL="..." \
  EMAIL_USER="..." \
  EMAIL_PASS="..." \
  LIVEKIT_API_KEY="..." \
  LIVEKIT_API_SECRET="..." \
  ALLOWED_ORIGINS="https://your-frontend-url.vercel.app"

# Deploy
fly deploy
```

### Deploy Agent

```bash
cd agent

# Initialize Fly app
fly launch

# Configure as background worker
# Set environment variables
fly secrets set LIVEKIT_URL="wss://..." \
  LIVEKIT_API_KEY="..." \
  LIVEKIT_API_SECRET="..." \
  OPENAI_API_KEY="..." \
  BACKEND_URL="https://restaurant-booking-backend.fly.dev"

# Deploy
fly deploy
```

### Frontend on Vercel

Same as Option 1 - deploy frontend to Vercel (free, excellent).

---

## Option 3: Netlify (Alternative Frontend)

If you prefer Netlify over Vercel:

1. Go to [netlify.com](https://netlify.com) and sign up with GitHub
2. Click **"Add new site"** → **"Import an existing project"**
3. Connect your GitHub repository
4. Configure:
   - **Base directory**: `frontend`
   - **Build command**: `npm run build`
   - **Publish directory**: `frontend/build`

5. Add Environment Variables in **Site settings** → **Environment variables**:
   ```
   REACT_APP_LIVEKIT_URL=wss://your-project.livekit.cloud
   REACT_APP_BACKEND_URL=https://restaurant-booking-backend.onrender.com
   ```

6. Click **"Deploy site"**

---

## Platform Comparison

| Platform | Free Tier | Always-On | Setup Difficulty | Best For |
|----------|-----------|-----------|------------------|----------|
| **Render** | ✅ Yes | ⚠️ Sleeps | ⭐⭐⭐⭐⭐ Easy | Free deployment |
| **Vercel** | ✅ Yes | ✅ Yes | ⭐⭐⭐⭐⭐ Easy | Frontend hosting |
| **Netlify** | ✅ Yes | ✅ Yes | ⭐⭐⭐⭐⭐ Easy | Frontend hosting |
| **Fly.io** | ✅ Yes | ✅ Yes | ⭐⭐⭐ Medium | Always-on services |
| **Railway** | ⚠️ $5 credit | ✅ Yes | ⭐⭐⭐⭐⭐ Easy | Paid option |

---

## Recommended Free Setup

### 🏆 Best Free Option: Render + Vercel

1. **Backend**: Render free tier
2. **Agent**: Render free tier  
3. **Frontend**: Vercel (free, excellent)
4. **Database**: MongoDB Atlas (free forever)
5. **LiveKit**: LiveKit Cloud (free 1,000 min/month)

**Total: $0/month** ✅

**Note**: Render free tier services sleep after 15 min inactivity. First request after sleep takes ~30 seconds to wake up.

### 🚀 Always-On Free Option: Fly.io + Vercel

1. **Backend**: Fly.io free tier (always-on)
2. **Agent**: Fly.io free tier (always-on)
3. **Frontend**: Vercel (free)
4. **Database**: MongoDB Atlas (free)
5. **LiveKit**: LiveKit Cloud (free)

**Total: $0/month** ✅ (services never sleep!)

---

## Environment Variables Summary

### Backend (Render/Fly.io)
```
MONGODB_URI=mongodb+srv://...
OPENWEATHER_API_KEY=...
RESTAURANT_LOCATION=Mumbai
RESTAURANT_EMAIL=...
EMAIL_USER=...
EMAIL_PASS=...
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
PORT=5000
NODE_ENV=production
ALLOWED_ORIGINS=https://your-frontend.vercel.app,http://localhost:3000
```

### Agent (Render/Fly.io)
```
LIVEKIT_URL=wss://your-project.livekit.cloud
LIVEKIT_API_KEY=...
LIVEKIT_API_SECRET=...
OPENAI_API_KEY=...
BACKEND_URL=https://restaurant-booking-backend.onrender.com
```

### Frontend (Vercel/Netlify)
```
REACT_APP_LIVEKIT_URL=wss://your-project.livekit.cloud
REACT_APP_BACKEND_URL=https://restaurant-booking-backend.onrender.com
```

---

## Post-Deployment Checklist

- [ ] Backend is accessible and returning API responses
- [ ] Agent is running and connecting to LiveKit
- [ ] Frontend loads and connects to backend
- [ ] Voice interaction works end-to-end
- [ ] MongoDB connection is working
- [ ] Email confirmations are being sent
- [ ] CORS is configured correctly (check `ALLOWED_ORIGINS`)
- [ ] Environment variables are set correctly
- [ ] All services are deployed and running

---

## Troubleshooting

### Backend Issues
- Check logs in Render/Fly.io dashboard
- Verify MongoDB connection string
- Ensure `PORT` environment variable is set (Render auto-sets, Fly.io needs explicit)
- Check CORS configuration (`ALLOWED_ORIGINS`)

### Agent Issues
- Verify LiveKit credentials
- Check OpenAI API key
- Ensure `BACKEND_URL` points to deployed backend URL
- Check Python version (3.9+)
- Verify agent is connecting to LiveKit Cloud

### Frontend Issues
- Verify environment variables are prefixed with `REACT_APP_`
- Check backend URL is correct and accessible
- Ensure build completes successfully
- Check browser console for CORS errors
- Verify LiveKit URL is correct

### Render Free Tier "Sleeping" Issue
- First request after 15 min inactivity takes ~30 seconds
- Upgrade to Starter plan ($7/month) for always-on
- Or use Fly.io for always-on free tier

---

## Cost Breakdown

### Free Tier (Recommended)
- **Render Backend**: Free (sleeps after 15 min)
- **Render Agent**: Free (sleeps after 15 min)
- **Vercel Frontend**: Free (always-on)
- **MongoDB Atlas**: Free (M0 cluster)
- **LiveKit Cloud**: Free (1,000 min/month)
- **Total**: **$0/month** ✅

### Always-On Free Tier (Fly.io)
- **Fly.io Backend**: Free (always-on, 3 VMs limit)
- **Fly.io Agent**: Free (always-on, 3 VMs limit)
- **Vercel Frontend**: Free (always-on)
- **MongoDB Atlas**: Free
- **LiveKit Cloud**: Free
- **Total**: **$0/month** ✅

### Paid Option (Always-On)
- **Render Starter**: $7/month × 2 services = $14/month
- **Vercel Frontend**: Free
- **MongoDB Atlas**: Free
- **LiveKit Cloud**: Free (or pay per minute after 1,000)
- **Total**: **$14/month**

---

## Quick Start Commands

### Render Deployment
1. Sign up at [render.com](https://render.com)
2. Connect GitHub repo
3. Create Web Service (backend)
4. Create Background Worker (agent)
5. Deploy frontend to Vercel

### Fly.io Deployment
```bash
# Install CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Deploy backend
cd backend && fly launch && fly secrets set ... && fly deploy

# Deploy agent
cd agent && fly launch && fly secrets set ... && fly deploy
```

---

## Need Help?

- **Render Docs**: [render.com/docs](https://render.com/docs)
- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **Fly.io Docs**: [fly.io/docs](https://fly.io/docs)
- **Netlify Docs**: [docs.netlify.com](https://docs.netlify.com)

