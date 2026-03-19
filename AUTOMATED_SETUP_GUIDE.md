# Automated Setup Guide

## Overview

The Medical Research RAG installer now includes **automated post-installation setup** that handles all the complex first-time configuration automatically!

---

## What Gets Automated?

When users check **"Complete setup now"** at the end of installation, the system automatically:

1. ✅ **Starts Docker containers** - Builds and launches the application
2. ✅ **Downloads AI models** - Gets nomic-embed-text (274MB) and deepseek-r1:7b (4.7GB)
3. ✅ **Waits for Ollama service** - Ensures everything is ready
4. ✅ **Waits for application** - Ensures web server is healthy
5. ✅ **Auto-ingests PDFs** - Processes 18 sample medical research papers (happens in background)
6. ✅ **Opens web browser** - Launches http://localhost:8000
7. ✅ **Ready to query!** - Application is fully configured with data ready

**Total time:** 15-40 minutes (depending on internet speed)
- Model download: 10-30 minutes
- PDF ingestion: 5-10 minutes (runs in background)

**User intervention:** None! Just check the box and wait.

---

## Installation Flow

### Option 1: Automated Setup (Recommended)

```
1. User runs MedicalResearchRAG_Setup.exe
2. Installation wizard completes
3. User sees checkbox: ☑ "Complete setup now (download AI models, ~5GB, 10-30 min)"
4. User checks the box and clicks Finish
5. POST_INSTALL_SETUP.bat runs automatically:
   ├─ Checks Docker is running
   ├─ Starts containers with: docker compose up -d --build
   ├─ Waits for Ollama service to be ready
   ├─ Downloads nomic-embed-text model (274MB)
   ├─ Downloads deepseek-r1:7b model (4.7GB)
   ├─ Waits for web application to be healthy
   ├─ Opens browser to http://localhost:8000
   └─ Auto-ingestion runs in background (18 PDFs)
6. User can immediately see the interface and watch ingestion progress!
7. After 5-10 minutes, all PDFs are processed and ready to query!
```

**Pros:**
- ✅ Zero manual configuration
- ✅ Everything ready in one go
- ✅ User can walk away and come back when done

**Cons:**
- ⏰ Takes 10-30 minutes
- 📶 Requires good internet connection
- 💻 User must have Docker Desktop already running

### Option 2: Manual Setup (For Advanced Users)

```
1. User runs MedicalResearchRAG_Setup.exe
2. Installation wizard completes
3. User unchecks/skips the automated setup
4. User manually runs from Start Menu:
   • Medical Research RAG → Complete Setup (First Time)
   OR
   • Medical Research RAG → Download AI Models (after starting the app)
```

**Pros:**
- ✅ Install quickly, set up later
- ✅ Can ensure Docker is ready first
- ✅ More control over timing

**Cons:**
- ⏰ Requires extra step
- 📋 User needs to remember to do it

---

## Files Added/Modified

### New Files:

1. **POST_INSTALL_SETUP.bat** - Automated setup script
   - Checks Docker is running
   - Starts containers
   - Downloads AI models
   - Opens browser
   - Provides clear status messages

### Modified Files:

1. **installer.iss** - Installer configuration
   - Added POST_INSTALL_SETUP.bat to [Files] section
   - Added "Complete Setup (First Time)" shortcut to Start Menu
   - Added post-install checkbox option to run setup automatically

2. **WINDOWS_INSTALLER_README.txt** - User documentation
   - Updated "First Time Setup" section
   - Added automated setup instructions
   - Updated shortcuts list

---

## What Happens Behind the Scenes

### Step 1: Docker Check (Instant)
```batch
docker info >nul 2>&1
if errorlevel 1 (
    echo Docker Desktop is not running!
    echo Please start Docker Desktop and run setup again.
)
```

### Step 2: Build Containers (5-10 minutes first time)
```batch
docker compose up -d --build
```
- Downloads base Docker images (Python, Ollama)
- Installs Python dependencies
- Builds custom images
- Starts both containers (ollama + rag-app)

### Step 3: Wait for Ollama (10-60 seconds)
```batch
# Polls until Ollama service responds
docker compose exec -T ollama ollama list
```

### Step 4: Download Models (10-30 minutes)
```batch
# Embedding model (274MB) - 2-5 minutes
docker compose exec -T ollama ollama pull nomic-embed-text

# LLM model (4.7GB) - 10-30 minutes
docker compose exec -T ollama ollama pull deepseek-r1:7b
```

### Step 5: Wait for Application (10-120 seconds)
```batch
# Polls until web server responds
curl -s http://localhost:8000/health
```

### Step 6: Launch Browser (Instant)
```batch
start http://localhost:8000
```

### Step 7: Auto-Ingestion (5-10 minutes, background)
- Application automatically processes all PDFs in pdfs/ folder
- User can see progress in web interface (Ingest tab)
- 18 sample medical research papers = ~862 chunks
- Happens in background while user explores the interface

---

## User Experience

### What Users See:

**During Installation:**
```
┌─────────────────────────────────────────────┐
│ Setup - Completing Installation            │
├─────────────────────────────────────────────┤
│                                             │
│ Setup has finished installing Medical      │
│ Research RAG Pipeline on your computer.     │
│                                             │
│ ☑ View Setup Instructions                  │
│ ☑ Complete setup now (download AI models,  │
│   ~5GB, 10-30 min)                         │
│                                             │
│              [ Finish ]                     │
└─────────────────────────────────────────────┘
```

**After Clicking Finish (if box checked):**
```cmd
========================================
 Medical Research RAG Pipeline
 Post-Installation Setup
========================================

[Step 1/4] Docker Desktop detected...

[Step 2/4] Starting Docker containers...
This will build the application (may take 5-10 minutes first time)...
[+] Building 234.5s (12/12) FINISHED
[+] Running 2/2
 ✔ Container medical-rag-ollama    Started
 ✔ Container medical-rag-app       Started

[Step 3/4] Waiting for Ollama service to be ready...
Ollama service is ready!

[Step 4/4] Downloading AI models (approximately 5GB)...
This may take 10-30 minutes depending on your internet speed.

You can minimize this window - the download will continue in the background.

Downloading embedding model (nomic-embed-text, 274MB)...
pulling manifest
pulling 970aa74c0a90... 100% ▕████████████▏ 274 MB
verifying sha256 digest
writing manifest
success

Downloading LLM model (deepseek-r1:7b, 4.7GB)...
This is the large language model - this will take a while...

pulling manifest
pulling 4e682fb19a38... 100% ▕████████████▏ 4.7 GB
verifying sha256 digest
writing manifest
success

[Step 5/5] Auto-ingesting sample PDFs...
The application will automatically process the 18 sample medical research papers.
This ensures everything is ready when you start querying!

Waiting for application to be ready...

Auto-ingestion is running in the background...
You can check progress in the web interface.

This may take 5-10 minutes. The browser will open when ready.

Waiting for application to start... (5/24)
Application is running! Auto-ingestion in progress...

========================================
 Setup Complete!
========================================

The Medical Research RAG application is now running.

IMPORTANT:
 • Auto-ingestion is running in the background
 • 18 sample medical research PDFs are being processed
 • You can start querying once ingestion completes (~5-10 minutes)
 • Check the Ingest tab to see progress

Opening the application in your browser...

You can access the application at: http://localhost:8000

To start/stop the application, use the shortcuts in the Start Menu:
  - Start Medical RAG
  - Stop Medical RAG
  - Check Status

The setup will complete in the background.
Feel free to close this window or minimize it.

Press any key to continue . . .
```

**Browser Opens:**
- User sees the web interface at http://localhost:8000
- **Ingest tab** shows real-time progress: "Processing PDF 3/18..."
- User can watch as PDFs are ingested
- After 5-10 minutes, all 18 PDFs processed (862 chunks total)
- **Query tab** becomes fully functional - ready to ask questions!
- Can immediately query the sample medical research papers!

---

## Troubleshooting

### Issue: "Docker Desktop is not running"

**Solution:**
1. Start Docker Desktop from Start Menu
2. Wait for green whale icon in system tray
3. Run setup again: Start Menu → Medical Research RAG → Complete Setup (First Time)

### Issue: "Failed to download models"

**Possible causes:**
- No internet connection
- Firewall blocking Docker
- Docker Hub rate limiting (rare)

**Solution:**
1. Check internet connection
2. Run setup again (it will skip already-downloaded models)
3. Or download manually: Start Menu → Medical Research RAG → Download AI Models

### Issue: Setup times out waiting for Ollama

**Solution:**
1. Check Docker Desktop has enough resources:
   - Docker Desktop → Settings → Resources
   - CPU: 4+ cores
   - Memory: 8GB+
2. Restart Docker Desktop
3. Run setup again

### Issue: User wants to skip model download

**Solution:**
- Models can be downloaded later using Start Menu → Download AI Models
- Application will still work, but queries will fail until models are downloaded

---

## Manual Setup (If Automated Fails)

If automated setup fails for any reason, users can set up manually:

```batch
# 1. Navigate to installation folder
cd "C:\Program Files\MedicalResearchRAG"

# 2. Start containers
docker compose up -d --build

# 3. Download models
docker compose exec ollama ollama pull nomic-embed-text
docker compose exec ollama ollama pull deepseek-r1:7b

# 4. Open browser
start http://localhost:8000
```

Or use the Start Menu shortcuts:
1. Start Medical RAG
2. Download AI Models
3. Open Web Interface

---

## Benefits

### For End Users:
- ✅ One-click setup - check a box and walk away
- ✅ No technical knowledge required
- ✅ Application ready when setup completes
- ✅ Clear progress messages
- ✅ Can still do manual setup if preferred

### For Developers/Support:
- ✅ Fewer support requests
- ✅ Consistent setup experience
- ✅ Easy to test and verify
- ✅ Logs show exactly what happened
- ✅ Fallback to manual setup always available

### For Distribution:
- ✅ Professional installation experience
- ✅ Competitive with commercial software
- ✅ Users more likely to complete setup
- ✅ Better first impression

---

## Testing the Automated Setup

### On Windows:

1. **Build installer:**
   ```batch
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
   ```

2. **Install with automation:**
   ```batch
   cd installer_output
   MedicalResearchRAG_Setup.exe
   # Check the "Complete setup now" box at the end
   ```

3. **Verify:**
   - Setup window appears and runs for 10-30 minutes
   - Models download successfully
   - Browser opens to http://localhost:8000
   - Can query the sample PDFs

4. **Test manual shortcut:**
   - Uninstall and reinstall (skip automated setup)
   - Start Menu → Complete Setup (First Time)
   - Should work identically

---

## Summary

**Before:** Users had to manually start containers, download models, figure out commands

**After:** Users check one box and everything happens automatically

**User Experience:** ⭐⭐⭐⭐⭐ Professional, polished, "just works"

🚀 **Ready for distribution!**
