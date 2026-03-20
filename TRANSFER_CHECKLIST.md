# Transfer Checklist - Mac to Windows

**Date:** 2026-03-19
**Commit:** 2fcf23c

---

## Quick Transfer Guide

### Option 1: Transfer Entire Project (Recommended)

**Method:** USB drive, OneDrive, or email zip file

1. **Create ZIP file:**
   ```bash
   cd /Users/User
   zip -r healthcare-project-v2.zip "healthcare project"
   ```

2. **Transfer to Windows**

3. **Extract on Windows:**
   ```powershell
   # Extract to desired location
   # Example: C:\projects\healthcare-project
   ```

4. **Copy to installation folder:**
   ```powershell
   # Copy all files to installer location
   xcopy /E /I "C:\projects\healthcare-project\*" "C:\path\to\installer-location\"
   ```

---

### Option 2: Transfer Only Critical Files (Faster)

If you only want to update the installer project on Windows, transfer these **10 files**:

#### Core Application Files (5):
- [ ] `src/rag_pipeline.py` - Fixed query Ollama connection
- [ ] `src/ingestion_progress.py` - Fixed persistence tracking
- [ ] `api/query.py` - Fixed response parameter bug
- [ ] `app.py` - Enhanced status endpoint
- [ ] `static/index.html` - GUI improvements + query spinner fix

#### Installer Files (2):
- [ ] `POST_INSTALL_SETUP.bat`
- [ ] `installer.iss`

#### Documentation (4):
- [ ] `WINDOWS_INSTALLER_README.txt`
- [ ] `COMPLETE_UPDATE_SUMMARY.md`
- [ ] `WINDOWS_UPDATE_INSTRUCTIONS.md`
- [ ] `BUGFIX_QUERY_SPINNER.md` - NEW: Query spinner fix guide

**Windows Destination:**
```
C:\path\to\installer-location\
├── src\
│   ├── rag_pipeline.py           ← Replace
│   └── ingestion_progress.py     ← Replace
├── api\
│   └── query.py                  ← Replace
├── static\
│   └── index.html                ← Replace
├── app.py                        ← Replace
├── POST_INSTALL_SETUP.bat        ← New file
├── installer.iss                 ← Replace
└── WINDOWS_INSTALLER_README.txt  ← Replace
```

---

## After Transfer: Testing Steps

### Step 1: Test Locally (Before Building Installer)

```powershell
# Navigate to project
cd "C:\path\to\installer-location"

# Stop containers if running
docker compose down

# Rebuild with no cache
docker compose build --no-cache

# Start containers
docker compose up -d

# Watch logs
docker compose logs -f rag-app
```

**Expected Output:**
```
✓ Successfully connected to Ollama at http://ollama:11434
✓ Embedding model 'nomic-embed-text' is available
✓ Auto-ingestion: Processing 1-s2.0-S000293432100512X-main.pdf (1/18)
✓ Auto-ingestion: Successfully processed ... (X chunks)
...
✓ Auto-ingestion complete! Processed 18 PDFs
```

**Time:** ~5-10 minutes for ingestion

### Step 2: Test Web Interface

1. Open browser: http://localhost:8000

2. **Check Ingest Tab:**
   - Should show "18 Files Ingested"
   - Green checkmarks for all PDFs
   - List of successfully ingested files

3. **Test Query Tab:**
   - Ask: "What are the risk factors for stroke?"
   - Should get AI-generated answer with citations
   - Should show source PDFs with page numbers

4. **Check Metrics Tab:**
   - Should show 862 documents in database
   - Should show 18 unique files

### Step 3: Test Restart Persistence

```powershell
# Restart containers
docker compose restart

# Watch logs
docker compose logs -f rag-app
```

**Expected Output:**
```
ℹ Auto-ingestion: All 18 PDFs already ingested. Ready to query.
```

**Time:** ~10-20 seconds (instant startup, no re-ingestion)

### Step 4: Test GUI Improvements

1. Refresh browser: http://localhost:8000

2. **Ingest Tab should show:**
   - Summary dashboard: "18 Files Ingested"
   - Banner: "All 18 PDFs already ingested. Ready to query."
   - Green background banner (not blue)
   - Scrollable list of all 18 PDFs with checkmarks

3. **Add a new PDF and restart:**
   ```powershell
   # Copy a new PDF to pdfs folder
   copy "test.pdf" "pdfs\"

   # Restart
   docker compose restart
   ```

4. **Should see:**
   - Banner: "Processing 1 new files (18 already ingested)..."
   - File list updates in real-time
   - After ingestion: "19 Files Ingested"

---

## After Testing: Build Installer

### Step 1: Build Installer with Inno Setup

```powershell
# Open Inno Setup Compiler
# File -> Open -> installer.iss
# Build -> Compile

# Or command line:
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

**Output:** `installer_output\MedicalResearchRAG_Setup.exe`

### Step 2: Test Installer

**Clean Test Environment:**
- Fresh Windows machine or VM
- Docker Desktop installed and running
- No previous installation

**Installation Steps:**
1. Run `MedicalResearchRAG_Setup.exe`
2. Complete installation wizard
3. **Check the box:** ☑ "Complete setup now (download AI models, ~5GB, 10-30 min)"
4. Click Finish
5. Wait for automated setup (15-40 minutes)

**Expected Results:**
- Terminal window shows progress
- Downloads embedding model (274MB)
- Downloads LLM model (4.7GB)
- Browser opens automatically to http://localhost:8000
- Ingest tab shows real-time ingestion progress
- After 5-10 minutes: "All 18 PDFs ingested!"
- Query tab works immediately

### Step 3: Test Restart After Installation

```powershell
# Restart Docker containers
docker compose restart

# Or restart Docker Desktop entirely
```

**Expected:**
- Logs show: "All 18 PDFs already ingested. Ready to query."
- No re-ingestion occurs
- Application ready in 10-20 seconds
- GUI shows "18 Files Ingested" immediately

---

## Troubleshooting During Transfer

### Issue: Files missing on Windows

**Check:**
```powershell
# Verify all files exist
dir src\rag_pipeline.py
dir src\ingestion_progress.py
dir api\query.py
dir app.py
dir static\index.html
dir POST_INSTALL_SETUP.bat
dir installer.iss
dir WINDOWS_INSTALLER_README.txt
```

**Solution:** Re-transfer any missing files

### Issue: Docker build fails

**Solution:**
```powershell
# Clear Docker cache
docker system prune -a

# Confirm removal (Y)

# Rebuild
docker compose build --no-cache
docker compose up -d
```

### Issue: PDFs still re-ingesting

**Cause:** Old `src/ingestion_progress.py` still in use

**Check:**
```powershell
# Open src\ingestion_progress.py
# Line 136 should have:
# "processed_files": list(self.processed_files),
```

**Solution:** Replace file and rebuild

### Issue: Query returns 500 error

**Cause:** Old `api/query.py` still in use

**Check:**
```powershell
# Open api\query.py
# Line 121 should have:
# query_request.return_context
# NOT: request.return_context
```

**Solution:** Replace file and rebuild

### Issue: GUI doesn't show file list

**Cause:** Old `static/index.html` still in use or browser cache

**Solution:**
```powershell
# 1. Verify file was replaced
# 2. Hard refresh browser: Ctrl + Shift + R
# 3. Clear browser cache if needed
```

---

## File Verification

### Check Git Commit on Mac:

```bash
cd "/Users/User/healthcare project"
git log --oneline -1
# Should show: 2fcf23c Complete RAG system improvements...

git show --stat
# Should show 14 files changed, 2537 insertions(+), 25 deletions(-)
```

### Verify File Contents on Windows:

**src/rag_pipeline.py:**
- Line 38 should have: `base_url: str | None = None`
- Line 61 should have: `self.ollama_client = ollama.Client(host=self.base_url)`
- Line 185 should use: `self.ollama_client.chat(...)`

**src/ingestion_progress.py:**
- Line 136 should include: `"processed_files": list(self.processed_files),`

**api/query.py:**
- Line 121 should have: `query_request.return_context`

**POST_INSTALL_SETUP.bat:**
- Should be 177 lines
- Should have all 5 setup steps

**static/index.html:**
- Should have new "PDF Ingestion Status" section
- Should have `updateFileStatus()` function
- Should call updateFileStatus every 5 seconds

---

## Checklist Summary

### Before Transfer:
- [x] All changes committed on Mac (commit 2fcf23c)
- [ ] Create ZIP file of entire project
- [ ] Transfer to Windows

### On Windows - Local Testing:
- [ ] Extract/copy files to installer location
- [ ] Verify all 10 critical files present
- [ ] Rebuild Docker: `docker compose build --no-cache`
- [ ] Start containers: `docker compose up -d`
- [ ] Verify auto-ingestion completes (18 PDFs)
- [ ] Test query functionality
- [ ] Restart containers
- [ ] Verify no re-ingestion (instant startup)
- [ ] Check GUI shows "18 already ingested"

### Build Installer:
- [ ] Run Inno Setup Compiler on installer.iss
- [ ] Verify output: installer_output\MedicalResearchRAG_Setup.exe

### Test Installer:
- [ ] Run installer on clean Windows machine
- [ ] Check "Complete setup now" option
- [ ] Wait for automated setup (15-40 min)
- [ ] Verify browser opens automatically
- [ ] Watch ingestion progress in GUI
- [ ] Test query functionality
- [ ] Restart Docker
- [ ] Verify instant startup (no re-ingestion)
- [ ] Add new PDF, restart, verify only new file processed

### Distribution:
- [ ] Copy installer to distribution location
- [ ] Update GitHub Release (if applicable)
- [ ] Share with users

---

## Quick Reference

### File Sizes (For Verification):

| File | Approx. Size |
|------|--------------|
| src/rag_pipeline.py | ~12 KB |
| src/ingestion_progress.py | ~6 KB |
| api/query.py | ~5 KB |
| app.py | ~9 KB |
| static/index.html | ~35 KB |
| POST_INSTALL_SETUP.bat | ~5 KB |
| installer.iss | ~6 KB |
| WINDOWS_INSTALLER_README.txt | ~11 KB |

### Key Commands:

**Mac - Create ZIP:**
```bash
cd /Users/User
zip -r healthcare-project-v2.zip "healthcare project"
```

**Windows - Test:**
```powershell
docker compose down
docker compose build --no-cache
docker compose up -d
docker compose logs -f rag-app
```

**Windows - Build Installer:**
```powershell
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

---

## Support Documents

For detailed information, refer to:

1. **COMPLETE_UPDATE_SUMMARY.md** - Comprehensive overview of all changes
2. **WINDOWS_UPDATE_INSTRUCTIONS.md** - Step-by-step Windows update guide
3. **AUTOMATED_SETUP_GUIDE.md** - Developer documentation for automated setup
4. **GUI_IMPROVEMENTS_SUMMARY.md** - GUI enhancement details
5. **CRITICAL_FIX_SUMMARY.md** - Bug fix documentation

---

## Success Criteria

After completing the checklist, you should have:

✅ Installer that runs automated setup with one checkbox
✅ No re-ingestion on container restarts (instant startup)
✅ Clear GUI showing which PDFs are ingested
✅ Working query functionality with AI-generated answers
✅ Professional installation experience ready for distribution

**Estimated Total Time:** 1-2 hours for complete transfer and testing

🚀 **Ready to go!**
