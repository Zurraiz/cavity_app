# Google Cloud Run Deployment Guide

## Prerequisites

1. **Google Cloud Account**
   - Go to https://cloud.google.com/
   - Sign up (you get $300 free credit for 90 days)
   - Create a new project or select an existing one

2. **Install Google Cloud CLI**
   - Download from: https://cloud.google.com/sdk/docs/install
   - Or use PowerShell:
   ```powershell
   (New-Object Net.WebClient).DownloadFile("https://dl.google.com/dl/cloudsdk/channels/rapid/GoogleCloudSDKInstaller.exe", "$env:Temp\GoogleCloudSDKInstaller.exe")
   & $env:Temp\GoogleCloudSDKInstaller.exe
   ```

3. **Install Docker Desktop** (for local testing)
   - Download from: https://www.docker.com/products/docker-desktop
   - Install and start Docker Desktop

---

## Step-by-Step Deployment

### Step 1: Initialize Google Cloud

Open PowerShell in your project directory and run:

```powershell
# Login to Google Cloud
gcloud auth login

# Set your project ID (replace PROJECT_ID with your actual project ID)
gcloud config set project PROJECT_ID

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

### Step 2: Test Docker Locally (Optional but Recommended)

```powershell
# Build the Docker image
docker build -t yolov8-caries-detector .

# Run locally to test
docker run -p 8080:8080 yolov8-caries-detector

# Open browser to http://localhost:8080 to test
# Press Ctrl+C to stop when done
```

### Step 3: Deploy to Cloud Run

```powershell
# Deploy (this will build and deploy in one command)
gcloud run deploy yolov8-caries-detector `
  --source . `
  --region us-central1 `
  --platform managed `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2 `
  --timeout 300 `
  --max-instances 10
```

**What this does:**
- `--source .` - Builds from your current directory
- `--region us-central1` - Deploys to US Central region (change if needed)
- `--allow-unauthenticated` - Makes it publicly accessible
- `--memory 2Gi` - Allocates 2GB RAM (needed for your models)
- `--cpu 2` - Allocates 2 CPU cores for better performance
- `--timeout 300` - 5-minute timeout for requests
- `--max-instances 10` - Limits concurrent instances

### Step 4: Get Your URL

After deployment completes, you'll see:

```
Service [yolov8-caries-detector] revision [yolov8-caries-detector-00001-xxx] has been deployed and is serving 100 percent of traffic.
Service URL: https://yolov8-caries-detector-xxxxxxxxxxxx-uc.a.run.app
```

**Copy this URL** - that's your live application! 🎉

---

## Cost Estimation

**Free Tier Includes:**
- 2 million requests/month
- 360,000 GB-seconds/month
- 180,000 vCPU-seconds/month

**Your App Usage (2GB RAM, 2 CPU):**
- Cost per request: ~$0.0001-0.0005 (depending on processing time)
- **100 requests/day**: ~$1-3/month
- **1,000 requests/day**: ~$10-30/month

**Most likely: $0-5/month for personal/demo use**

---

## Alternative: Deploy from GitHub

If you push your code to GitHub, you can also deploy directly:

```powershell
gcloud run deploy yolov8-caries-detector `
  --source https://github.com/YOUR_USERNAME/yolov8_caries_detector `
  --region us-central1 `
  --platform managed `
  --allow-unauthenticated `
  --memory 2Gi `
  --cpu 2
```

---

## Useful Commands

### View logs:
```powershell
gcloud run services logs read yolov8-caries-detector --limit 50
```

### Update deployment:
```powershell
gcloud run deploy yolov8-caries-detector --source .
```

### Delete service:
```powershell
gcloud run services delete yolov8-caries-detector
```

### Check service status:
```powershell
gcloud run services describe yolov8-caries-detector
```

---

## Troubleshooting

### Build fails with timeout:
Increase build timeout:
```powershell
gcloud config set builds/timeout 1800
```

### Out of memory errors:
Increase memory to 4Gi:
```powershell
gcloud run deploy yolov8-caries-detector --memory 4Gi --source .
```

### Slow cold starts:
Enable minimum instances (costs more):
```powershell
gcloud run services update yolov8-caries-detector --min-instances 1
```

---

## Security (Optional)

### Require authentication:
```powershell
gcloud run deploy yolov8-caries-detector --no-allow-unauthenticated --source .
```

### Add custom domain:
```powershell
gcloud run domain-mappings create --service yolov8-caries-detector --domain yourdomain.com
```

---

## Next Steps

1. Deploy and test your application
2. Share the URL with users
3. Monitor usage in Google Cloud Console
4. Set up billing alerts to avoid surprises
5. Consider adding authentication for production use

**Need help?** Check the logs or Cloud Run documentation at:
https://cloud.google.com/run/docs
