# Deployment Guide — Making It All Live

## Overview

| Component | Platform | URL |
|-----------|----------|-----|
| Marketing site | GoDaddy Airo | `usahealthcare.ai` |
| Frontend app | Vercel | `app.usahealthcare.ai` |
| Backend API | Railway | `api.usahealthcare.ai` |

---

## Step 1: Deploy Backend on Railway (15 minutes)

### 1.1 Create Railway Account
1. Go to https://railway.app
2. Click "Login" → **Login with GitHub** (use your pkarakala account)
3. You're in. Free tier gives you $5/month credit (plenty for dev).

### 1.2 Create a New Project
1. Click **"New Project"**
2. Select **"Deploy from GitHub Repo"**
3. Pick **UnitedHealthCareAI**
4. Railway will detect files — it might try to deploy from root. We'll fix that.

### 1.3 Configure the Backend Service
1. Click on the service that was created
2. Go to **Settings** tab
3. Set:
   - **Root Directory:** `backend`
   - **Builder:** Dockerfile
4. Go to **Variables** tab and add:
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
   SECRET_KEY=generate-random-string
   ENCRYPTION_KEY=generate-32-char-string
   ENCRYPTION_SALT=generate-random-string   # keep constant; changing it breaks PHI decryption
   WEBHOOK_SECRET=generate-random-string    # inbound webhooks 503 until this is set
   CORS_ORIGINS=http://localhost:3000,https://app.usahealthcare.ai
   APP_ENV=production
   LOG_LEVEL=INFO
   SENTRY_DSN=                     # optional; enables error reporting (PII/bodies never sent)
   UPLOAD_DIR=/data/uploads        # required once the volume (1.3a) is attached
   ```

### 1.3a File storage — Railway Volume (required for production)

Uploaded documents/images are written to `UPLOAD_DIR` (default `uploads/`).
Railway's filesystem is **ephemeral** — without a volume, uploads are lost on
every redeploy. Mount a persistent volume:

1. In your Railway project, right-click the backend service → **"Attach Volume"**
   (or **Settings** → **Volumes** → **"Add Volume"**)
2. Set **Mount Path** to `/data/uploads`
3. Add the variable: `UPLOAD_DIR=/data/uploads`
4. Redeploy. Uploads now survive redeploys.

Note: a volume attaches to a single service instance (fine for the worker-less
or single-replica setup). `app/services/storage.py` is written to a storage
interface if an object-store backend is added later.

### 1.3b Worker service (required for scheduled tasks / async workflow)

The web service runs only uvicorn. Status polling, follow-ups, and
`ASYNC_WORKFLOW=true` all require a Celery worker:

1. In your Railway project, click **"+ New"** → **"Empty Service"**
2. Point it at the **same GitHub repo**, Root Directory `backend`,
   Builder Dockerfile
3. **Settings** → **Deploy** → **Custom Start Command:** `bash start-worker.sh`
   (runs Celery worker + beat in one process)
4. **Variables:** reference the same `DATABASE_URL`, `REDIS_URL`, and copy the
   same app secrets as the web service (`SECRET_KEY`, `ENCRYPTION_KEY`,
   `ENCRYPTION_SALT`, `ANTHROPIC_API_KEY`, `APP_ENV=production`)
5. If the volume from 1.3a is needed by worker tasks that touch uploads,
   note a Railway volume mounts to **one** service — keep upload handling in
   the web service, or move to an object store when both need it.

Once the worker is live you may set `ASYNC_WORKFLOW=true` on the web service
so the PA workflow runs out-of-band instead of inside the HTTP request.

> With async enabled and **no** worker, new PAs are queued but never
> processed — leave `ASYNC_WORKFLOW` unset unless the worker service exists.

### 1.4 Add PostgreSQL
1. In your Railway project, click **"+ New"** → **"Database"** → **"PostgreSQL"**
2. Railway auto-creates it and gives you a `DATABASE_URL`
3. Go to your backend service → **Variables**
4. Add: `DATABASE_URL` → click "Reference" → select the Postgres `DATABASE_URL` variable
   - Change `postgresql://` to `postgresql+asyncpg://` at the start

### 1.5 Add Redis
1. Click **"+ New"** → **"Database"** → **"Redis"**
2. Go to backend service → **Variables**
3. Add: `REDIS_URL` → Reference the Redis `REDIS_URL` variable

### 1.6 Deploy
1. Railway auto-deploys when you save variables
2. Check the **Deploy Logs** — should see "Uvicorn running on 0.0.0.0:8000"
3. Go to **Settings** → **Networking** → **Generate Domain**
4. You'll get something like: `unitedhealthcareai-production.up.railway.app`
5. Test it: visit `https://your-railway-url.up.railway.app/api/v1/health`

### 1.7 Run Migrations
1. In Railway, go to your backend service
2. Click **"New"** → **"Run Command"** (or use the Railway CLI)
3. Run: `alembic upgrade head`
4. Then: `python scripts/seed.py`

Or add this to your Dockerfile (before CMD):
```dockerfile
RUN alembic upgrade head
```

---

## Step 2: Connect Frontend to Backend (5 minutes)

### 2.1 Update Vercel Environment Variable
1. Go to https://vercel.com → Your project (united-health-care-ai)
2. **Settings** → **Environment Variables**
3. Add:
   - Name: `NEXT_PUBLIC_API_URL`
   - Value: `https://your-railway-url.up.railway.app` (the URL from step 1.6)
4. Click Save

### 2.2 Redeploy
1. Go to **Deployments** tab
2. Click the three dots on the latest deploy → **Redeploy**
3. Wait for it to build (~1 minute)

### 2.3 Test
1. Visit your Vercel URL
2. You should see the dashboard loading data from the backend
3. Try creating a patient and intaking a prescription

---

## Step 3: Connect Custom Domains (10 minutes)

### 3.1 Add `app.usahealthcare.ai` to Vercel
1. Vercel → Project → **Settings** → **Domains**
2. Type: `app.usahealthcare.ai`
3. Click Add
4. Vercel will show you the DNS record needed (CNAME → `cname.vercel-dns.com`)

### 3.2 Add `api.usahealthcare.ai` to Railway
1. Railway → Backend service → **Settings** → **Networking** → **Custom Domain**
2. Type: `api.usahealthcare.ai`
3. Railway will show you the DNS record needed

### 3.3 Add DNS Records in GoDaddy
1. Go to https://dcc.godaddy.com → **DNS** for `usahealthcare.ai`
2. Click **"Add Record"**

**Record 1 (Frontend):**
| Type | Name | Value | TTL |
|------|------|-------|-----|
| CNAME | app | cname.vercel-dns.com | 600 |

**Record 2 (Backend API):**
| Type | Name | Value | TTL |
|------|------|-------|-----|
| CNAME | api | (Railway gives you this value) | 600 |

3. Save. DNS propagation takes 5-30 minutes.

### 3.4 Update Backend CORS
After the domain is live, update Railway env var:
```
CORS_ORIGINS=https://app.usahealthcare.ai,http://localhost:3000
```

### 3.5 Update Frontend API URL
In Vercel env vars, update:
```
NEXT_PUBLIC_API_URL=https://api.usahealthcare.ai
```
Redeploy.

---

## Step 4: Link Marketing Site to App (2 minutes)

1. Go to your GoDaddy Airo builder
2. Find the **"Explore the Platform"** button
3. Set its link to: `https://app.usahealthcare.ai`
4. Find **"Request a Demo"** button
5. Set its link to: `https://app.usahealthcare.ai/login` (or a contact form)
6. Publish the Airo site

---

## Step 5: Verify Everything Works

```bash
# Check backend health
curl https://api.usahealthcare.ai/api/v1/health

# Check frontend loads
open https://app.usahealthcare.ai

# Check marketing site links to app
open https://usahealthcare.ai
```

---

## Final Architecture (Live)

```
User visits usahealthcare.ai
        │
        ├── Marketing pages (GoDaddy Airo)
        │
        └── Clicks "Explore the Platform"
                │
                ▼
        app.usahealthcare.ai (Vercel - Next.js)
                │
                │ API calls
                ▼
        api.usahealthcare.ai (Railway - FastAPI)
                │
                ├── PostgreSQL (Railway)
                ├── Redis (Railway)
                └── Claude API (Anthropic)
```

---

## Costs (Estimated Monthly)

| Service | Free Tier | After Free Tier |
|---------|-----------|-----------------|
| Vercel (frontend) | 100GB bandwidth | $20/mo Pro |
| Railway (backend + DB + Redis) | $5 credit/mo | ~$10-20/mo |
| Anthropic (Claude API) | $5 initial credit | ~$5-50/mo depending on usage |
| GoDaddy (domain) | Already paid ($320/yr) | — |
| **Total to start** | **$0** | **~$15-70/mo** |

---

## Troubleshooting

### Backend returns 500 errors
- Check Railway deploy logs
- Ensure `DATABASE_URL` uses `postgresql+asyncpg://` prefix
- Run `alembic upgrade head` to create tables

### Frontend shows "Loading..." forever
- Check browser console for CORS errors
- Verify `NEXT_PUBLIC_API_URL` is set correctly in Vercel
- Make sure backend `CORS_ORIGINS` includes the frontend URL

### Custom domain not working
- DNS can take up to 30 minutes to propagate
- Check with: `dig app.usahealthcare.ai CNAME`
- Make sure there's no conflicting A record

### "Connection refused" from frontend to backend
- Both need HTTPS in production
- Railway provides HTTPS automatically
- Vercel provides HTTPS automatically
- Don't use http:// in the API URL
