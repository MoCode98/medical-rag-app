# Automatic Ingestion During Installation

**Feature:** Sample PDFs are automatically ingested during the installation process
**Status:** ✅ Implemented
**Updated:** 2026-03-20

---

## Overview

The Windows installer now performs complete PDF ingestion during the initial setup, ensuring the system is immediately ready for queries when the user first opens the application.

---

## How It Works

### Installation Process

**Step 1-4:** Download Docker, build containers, download AI models (existing)

**Step 5:** Wait for application to be ready
- Polls `/health` endpoint until app is running
- Timeout: 2 minutes (120 seconds)

**Step 6:** Trigger ingestion
- Calls `POST /api/ingest` to start ingestion
- Processes all PDFs in the `pdfs/` folder (18 sample medical research papers)

**Step 7:** Wait for ingestion to complete
- Polls `/api/ingest/status` every 10 seconds
- Shows progress: elapsed time and files processed
- Timeout: 30 minutes (safety limit)
- Uses PowerShell script for reliable JSON parsing

### Files Involved

1. **POST_INSTALL_SETUP.bat** (Updated)
   - Main installation script
   - Steps 5-7 handle ingestion
   - Uses curl to trigger ingestion
   - Calls wait_for_ingestion.ps1

2. **wait_for_ingestion.ps1** (NEW)
   - PowerShell script for status monitoring
   - Parses JSON responses from API
   - Shows real-time progress
   - Returns exit code 0 on success

3. **installer.iss** (Updated)
   - Added `wait_for_ingestion.ps1` to files list
   - Added `docker-entrypoint.sh` to files list

---

## User Experience

### Before (Previous Behavior)

1. Install application
2. Run POST_INSTALL_SETUP.bat
3. Wait for models to download
4. Open browser
5. **Manually upload PDFs in GUI**
6. **Manually click "Start Ingestion"**
7. **Wait 5-10 minutes**
8. Finally ready to query

**Total clicks:** 3-4  
**Manual waiting:** Required  
**User action:** Upload + trigger ingestion

### After (New Behavior)

1. Install application
2. Check "Complete setup now" in installer
3. Wait (automated - downloads models + ingests PDFs)
4. Browser opens automatically
5. **Ready to query immediately!**

**Total clicks:** 1 (checkbox)  
**Manual waiting:** Optional (can minimize window)  
**User action:** None! Fully automated

---

## Technical Details

### API Endpoints Used

**Start Ingestion:**
```bash
POST http://localhost:8000/api/ingest
Content-Type: application/json
```

**Check Status:**
```bash
GET http://localhost:8000/api/ingest/status
```

**Response:**
```json
{
  "is_running": false,
  "complete": true,
  "files_processed": 18,
  "progress": 100,
  "message": "Ingestion complete"
}
```

### Progress Monitoring

The `wait_for_ingestion.ps1` script:

```powershell
# Polls every 10 seconds
# Shows elapsed time and files processed
# Example output:
Ingestion in progress... [2.5 min] Files: 8
```

### Timeout Handling

**Application startup timeout:** 2 minutes
- If app doesn't start, opens browser anyway with warning

**Ingestion timeout:** 30 minutes
- If ingestion exceeds 30 min, opens browser with warning
- User can monitor progress in web interface

---

## Installation Flow

### POST_INSTALL_SETUP.bat Flow

```
[Step 1/4] Check Docker
     ↓
[Step 2/4] Start Docker containers (docker compose up -d --build)
     ↓
[Step 3/4] Download AI models (ollama pull)
     ↓
[Step 4/4] Models downloaded
     ↓
[Step 5/7] Wait for application ready (health check)
     ↓
[Step 6/7] Trigger ingestion (curl POST /api/ingest)
     ↓
[Step 7/7] Wait for completion (wait_for_ingestion.ps1)
     ↓
[SUCCESS] Open browser → Ready to query!
```

### Timing

**Typical installation:**
- Docker containers: 5-10 minutes (first time)
- AI model download: 10-30 minutes (5GB)
- PDF ingestion: 5-10 minutes (18 papers)
- **Total:** 20-50 minutes

**Subsequent runs:**
- Containers already built: ~30 seconds
- Models already downloaded: skip
- Ingestion (if needed): 5-10 minutes

---

## Error Handling

### If Application Doesn't Start

```
[WARNING] Application did not start in expected time.
Opening browser anyway - you may need to refresh the page.
```

**User action:** Refresh browser, check Docker logs

### If Ingestion API Call Fails

```
[WARNING] Could not trigger ingestion automatically.
You can start ingestion manually from the web interface.
```

**User action:** Open Ingest tab, click "Start Ingestion"

### If Ingestion Times Out

```
⚠ Ingestion is taking longer than expected (>30 minutes)
  You can monitor progress in the web interface.
```

**User action:** Check web interface Ingest tab for progress

---

## Benefits

### For End Users

✅ **Zero manual steps** - Complete automation  
✅ **Immediate readiness** - System ready when browser opens  
✅ **Professional experience** - "It just works"  
✅ **No confusion** - No need to understand ingestion concept  
✅ **Instant gratification** - Can query immediately

### For Developers/Support

✅ **Zero support tickets** - "How do I add PDFs?"  
✅ **Consistent state** - Every installation has same sample data  
✅ **Better demos** - System is demo-ready instantly  
✅ **Reduced onboarding** - No training needed for basic usage

---

## Testing on Windows

### Full Installation Test

1. **Build installer:**
   ```powershell
   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
   ```

2. **Run installer:**
   ```powershell
   .\Output\MedicalResearchRAG_Setup.exe
   ```

3. **Check "Complete setup now"** (during install)

4. **Watch console output:**
   - Should show all 7 steps
   - Step 7 should show: "Ingestion in progress..."
   - Should complete with: "✓ Ingestion complete!"

5. **Browser opens automatically**

6. **Test query immediately:**
   - Query tab should work
   - Sources should return relevant chunks
   - No "upload PDFs first" message

### Manual Ingestion Test

If you need to test without the installer:

```powershell
cd "C:\Program Files\MedicalResearchRAG"

# Ensure app is running
docker compose up -d

# Wait for app to be ready
timeout /t 10

# Trigger ingestion manually
curl -X POST http://localhost:8000/api/ingest

# Monitor progress
powershell -ExecutionPolicy Bypass -File wait_for_ingestion.ps1 -MaxMinutes 30
```

---

## Verification Checklist

After installation completes:

- [ ] Browser opened automatically
- [ ] Application loads at http://localhost:8000
- [ ] Query tab is active and responsive
- [ ] Test query returns results (e.g., "What is diabetes?")
- [ ] Sources section shows context chunks
- [ ] Ingest tab shows "18 files ingested"
- [ ] No "upload PDFs" prompt

---

## Rollback (If Needed)

If automatic ingestion causes issues:

### Option 1: Skip Ingestion During Install

Edit POST_INSTALL_SETUP.bat, comment out Step 6-7:

```batch
REM echo [Step 6/7] Starting ingestion...
REM curl -X POST http://localhost:8000/api/ingest
REM powershell ... wait_for_ingestion.ps1 ...
```

### Option 2: Manual Ingestion Only

Keep installer as-is, but instruct users to:
1. Open http://localhost:8000
2. Go to Ingest tab
3. Upload PDFs (if needed)
4. Click "Start Ingestion"

---

## Future Enhancements

Possible improvements:

1. **Progress Bar** - Show visual progress in installer window
2. **Parallel Tasks** - Download models while ingesting
3. **Smart Skip** - Skip ingestion if already complete
4. **Custom PDFs** - Allow user to select PDFs during install
5. **Background Mode** - Continue ingestion after browser opens

---

## Files Modified

### POST_INSTALL_SETUP.bat
- **Lines 105-163:** Added Steps 5-7 for ingestion
- **Line 135:** Trigger ingestion via curl
- **Line 151:** Call wait_for_ingestion.ps1
- **Lines 196-200:** Updated success message

### wait_for_ingestion.ps1 (NEW)
- PowerShell script for reliable status monitoring
- JSON parsing with Invoke-RestMethod
- Real-time progress display
- Exit codes for success/failure

### installer.iss
- **Line 50:** Added docker-entrypoint.sh
- **Line 75:** Added wait_for_ingestion.ps1

---

## Summary

**Problem:** Users had to manually upload and ingest PDFs after installation  
**Solution:** Automatic ingestion during installation process  
**Result:** System is immediately ready for queries when browser opens  

**User Experience:**
- Before: 4 manual steps, 5-10 min waiting
- After: 1 click (checkbox), fully automated

**Installation Time:**
- First time: 20-50 minutes (includes ingestion)
- Subsequent: Same (ingestion already done)

**Support Impact:**
- Zero "how do I upload PDFs" tickets
- Professional, polished installation experience
- Users can query immediately

✅ **Ingestion during installation = Better user experience!**
