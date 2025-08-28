# 🚀 Deployment Guide

## Quick Deploy to Render (Free)

### Step 1: Prepare Your Code
1. Make sure all files are saved
2. Your project should have:
   - `app.py`
   - `requirements.txt`
   - `Procfile`
   - `README.md`
   - `sample_team.csv`

### Step 2: Upload to GitHub
1. Create a new repository on GitHub
2. Upload your files:
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
   git push -u origin main
   ```

### Step 3: Deploy on Render
1. Go to [render.com](https://render.com)
2. Sign up/Login with GitHub
3. Click "New Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Name**: `skahl-line-builder` (or any name you want)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python3 app.py`
6. Click "Create Web Service"
7. Wait for deployment (2-3 minutes)

### Step 4: Share with Friends
- Your app will be available at: `https://your-app-name.onrender.com`
- Share this URL with your friends!

## Alternative: Railway (Also Free)

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository
6. Railway will auto-detect it's a Python app
7. Deploy automatically

## Troubleshooting

### If the app doesn't start:
- Check the logs in Render/Railway dashboard
- Make sure `requirements.txt` has all dependencies
- Verify `Procfile` is correct

### If you get errors:
- Check that all files are uploaded to GitHub
- Make sure `app.py` has the correct port configuration
- Verify the build command is correct

## Cost
- **Render**: Free for 750 hours/month (perfect for friends)
- **Railway**: Free $5 credit monthly
- **Heroku**: $7/month minimum

## Support
If you need help, check the logs in your hosting platform's dashboard!
