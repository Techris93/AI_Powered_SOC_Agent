# Firebase Deployment Guide

## What is deployed

- Frontend only (static UI from `firebase_public/index.html`).
- Backend API (FastAPI) should be hosted separately (for example Cloud Run, VM, or another API host).

## 1. Create/select Firebase project

1. Open Firebase Console: https://console.firebase.google.com/u/0/
2. Create a new project (or pick an existing one).
3. Copy the project ID (Project settings > General).

## 2. Set Firebase project ID in this repo

This repo is currently configured for project ID `ai-powered-soc-agent`.

If you need to change it, update `.firebaserc`.

## 3. Login and deploy Hosting

Current repo defaults are intentionally unchanged:

- `.firebaserc` default project: `ai-powered-soc-agent`
- `firebase.json` hosting site: `ai-powered-soc-agent-ui`

From project root run one of these deploy paths.

### Option A: Deploy with current repo config (default path)

```bash
npx firebase-tools login
npx firebase-tools use ai-powered-soc-agent --add
npx firebase-tools deploy --only hosting --project ai-powered-soc-agent
```

### Option B: Deploy to alternate working project/site (override path)

This path was verified working when the default site returned Hosting API 500.

```bash
cat > firebase.temp.json << 'EOF'
{
	"hosting": {
		"site": "ai-powered-soc-agent-97d0c",
		"public": "firebase_public",
		"ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
		"rewrites": [
			{
				"source": "**",
				"destination": "/index.html"
			}
		]
	}
}
EOF

npx firebase-tools deploy --only hosting --config firebase.temp.json --project ai-powered-soc-agent-97d0c
rm -f firebase.temp.json
```

Current known issue:

- Firebase Hosting API is returning `HTTP 500 Internal error encountered` while creating Hosting versions for this project/site.
- Error occurs on endpoint: `POST /v1beta1/projects/-/sites/<site-id>/versions`.
- Authentication and IAM permissions are valid; failure is platform-side.

Recommended recovery actions:

1. Retry deployment after 10-30 minutes (transient backend issue is common).
2. Run deploy from another environment with Node 20+ and latest Firebase CLI.
3. Open Firebase support ticket and attach `firebase-debug.log` from this repo root.
4. Temporary fallback: deploy the static `firebase_public` folder from Firebase Console Hosting UI once service recovers.

## 4. Configure frontend API endpoint for production

The UI resolves API base in this order:

1. `window.SOC_API_BASE`
2. `localStorage.soc_api_base`
3. `http://localhost:5001/api` when on localhost
4. `<current-origin>/api` for hosted environments

If your backend is not hosted under the same domain as Firebase Hosting, set this once in browser console on your deployed site:

```javascript
localStorage.setItem("soc_api_base", "https://your-backend-domain/api");
location.reload();
```

## Optional: host API behind same domain

If you deploy FastAPI to Cloud Run, you can add a Firebase Hosting rewrite from `/api/**` to that Cloud Run service, then remove the localStorage override.

## Quick local verification

Run backend locally:

```bash
/Users/chrixchange/AI-Powered-SOCAgent/venv/bin/python main.py
```

Then open `firebase_public/index.html` with any static server and test API calls.
