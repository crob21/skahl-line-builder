# 🚀 SKAHL Line Builder - Deployment Guide

## Deploy to Render (Recommended)

### Step 1: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with your GitHub account
3. Verify your email

### Step 2: Deploy Your App
1. **Click "New +"** in your Render dashboard
2. **Select "Web Service"**
3. **Connect your GitHub repository**:
   - Choose your repository: `crob21/Projects`
   - Select branch: `hockey`
4. **Configure the service**:
   - **Name**: `skahl-line-builder` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: `Free`

### Step 3: Environment Variables (Optional)
Add these if needed:
- `PORT`: `10000` (Render will set this automatically)

### Step 4: Deploy
1. Click **"Create Web Service"**
2. Wait for the build to complete (2-3 minutes)
3. Your app will be available at: `https://your-app-name.onrender.com`

## Alternative Deployment Options

### Railway
1. Go to [railway.app](https://railway.app)
2. Connect GitHub repository
3. Deploy automatically

### Heroku
1. Install Heroku CLI
2. Run: `heroku create your-app-name`
3. Run: `git push heroku hockey:main`

### DigitalOcean App Platform
1. Go to [digitalocean.com](https://digitalocean.com)
2. Create new app from GitHub
3. Select your repository and branch

## Post-Deployment

### Test Your App
1. Visit your deployed URL
2. Test CSV upload functionality
3. Test team saving/loading
4. Test print functionality

### Share with Friends
- Send them the URL
- They can upload their own CSV files
- They can save their own team rosters

## Troubleshooting

### Common Issues:
- **Build fails**: Check requirements.txt is correct
- **App won't start**: Verify start command is `gunicorn app:app`
- **CSV upload fails**: Check file size limits (Render free tier: 100MB)

### Support:
- Render documentation: [docs.render.com](https://docs.render.com)
- Flask documentation: [flask.palletsprojects.com](https://flask.palletsprojects.com)

## Features Available After Deployment:
✅ **CSV Upload**: Upload SportNinja exports  
✅ **Team Management**: Save/load multiple teams  
✅ **Line Building**: Drag-and-drop interface  
✅ **Print Lines**: Professional line sheets  
✅ **Mobile Responsive**: Works on all devices  
✅ **Multi-user**: Everyone can use it simultaneously  

Your SKAHL Line Builder will be live and ready for your hockey team! 🏒
