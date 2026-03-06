<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# Run and deploy your AI Studio app

This contains everything you need to run your app locally.

View your app in AI Studio: https://ai.studio/apps/69bad4eb-85b2-4fde-a4f2-1f139eafe3a2

## Run Locally

**Prerequisites:**  Node.js


1. Install dependencies:
   `npm install`
2. Set the `GEMINI_API_KEY` in [.env.local](.env.local) to your Gemini API key
3. Run the app:
   `npm run dev`

## 🚀 Deployment (Vercel)

This dashboard is optimized for Vercel. 

### 1. Environment Variables
You MUST set these in your Vercel Project Settings:
- `MANYCHAT_API_KEY`: Your ManyChat API key.
- `GOOGLE_CLIENT_ID`: From Google Cloud Console.
- `GOOGLE_CLIENT_SECRET`: From Google Cloud Console.
- `ANTHROPIC_API_KEY`: (Optional) For AI Trends feature.
- `VITE_DEMO_USER_ID`: A unique ID for your data (or use the default).
- `APP_URL`: Your live Vercel URL (e.g., `https://my-dashboard.vercel.app`).

### 2. Database Notice
Vercel is **stateless**. The default SQLite database will reset if the server sleeps. 
- For permanent storage, add a `DATABASE_URL` for **Vercel Postgres** or **Supabase**.

### 3. Push to GitHub
1. Create a new GitHub repository.
2. `git init`
3. `git add .`
4. `git commit -m "Optimize for Vercel"`
5. `git push origin main`

### 4. Import to Vercel
- Import the repo. Vercel will auto-detect the `vercel.json` and build the app!
