# PDF Upload Troubleshooting Guide

**Issue:** File upload still not working after applying fix
**Updated:** 2026-03-20

---

## Latest Fix Applied

**Commit:** 7cd99ad - Simplified upload endpoint

**Changes:**
- Removed unused `Request` parameter
- Removed unused slowapi imports
- Cleaner, more robust implementation

---

## Step-by-Step Troubleshooting

### Step 1: Verify File Transfer

**On Windows, check that the updated file exists:**

```powershell
# Navigate to project
cd "C:\path\to\project"

# Check file was updated
Get-Content api\ingest.py | Select-String -Pattern "async def upload_pdfs"

# Should show:
# async def upload_pdfs(files: list[UploadFile] = File(...)) -> dict[str, Any]:
# (No "request: Request" parameter)
```

### Step 2: Rebuild Docker Container

**This is critical - backend changes require rebuild!**

```powershell
# Stop containers
docker compose down

# Rebuild with no cache (forces fresh build)
docker compose build --no-cache

# Start containers
docker compose up -d

# Watch logs for errors
docker compose logs -f rag-app
```

**Expected output:**
```
rag-app | INFO:     Started server process [1]
rag-app | INFO:     Waiting for application startup.
rag-app | INFO:     Application startup complete.
rag-app | INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 3: Test Upload in Browser

1. **Hard refresh browser:**
   ```
   Ctrl + Shift + R
   ```

2. **Open browser console:**
   ```
   Press F12 → Console tab
   ```

3. **Navigate to Ingest tab**

4. **Click "Upload PDF Files"**

5. **Select a small PDF file**

6. **Watch for errors in:**
   - Browser console (F12)
   - Docker logs (terminal running logs command)

### Step 4: Check Docker Logs for Errors

**In a separate terminal:**

```powershell
# Follow logs in real-time
docker compose logs -f rag-app

# Or just show recent errors
docker compose logs --tail=50 rag-app | Select-String -Pattern "error|Error|ERROR"
```

**Common error patterns and solutions below.**

---

## Common Errors and Fixes

### Error 1: "Cannot connect to Docker daemon"

**Symptom:**
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Cause:** Docker Desktop not running

**Solution:**
```powershell
# Start Docker Desktop from Start Menu
# Wait for green icon in system tray
# Try rebuild again
```

### Error 2: "ModuleNotFoundError" or "ImportError"

**Symptom:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Cause:** Dependencies not installed in container

**Solution:**
```powershell
# Full rebuild
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

### Error 3: "500 Internal Server Error" (still happening)

**Symptom:**
- Upload button clicked
- Progress bar shows
- Error: "Failed to load resources: 500 Internal Server Error"

**Check Docker logs:**
```powershell
docker compose logs --tail=100 rag-app
```

**Look for specific error message, then:**

**If you see "ValidationError":**
```python
# File might have invalid characters in name
# Try renaming file to simple name: test.pdf
```

**If you see "Permission denied":**
```powershell
# Check pdfs folder exists and is writable
docker compose exec rag-app ls -la /app/pdfs
```

**If you see "No such file or directory":**
```powershell
# Recreate volumes
docker compose down -v
docker compose up -d
```

### Error 4: Upload succeeds but file not in pdfs/ folder

**Symptom:**
- Upload shows success
- File not visible in pdfs/ folder
- Ingestion finds no new files

**Check volume mount:**
```powershell
# Check docker-compose.yml has correct volume mount
Get-Content docker-compose.yml | Select-String -Pattern "pdfs"

# Should show:
# - ./pdfs:/app/pdfs
```

**Recreate container:**
```powershell
docker compose down
docker compose up -d
```

### Error 5: "Request entity too large"

**Symptom:**
```
413 Request Entity Too Large
```

**Cause:** File exceeds max size (default: 50 MB)

**Solution:**
```powershell
# Check .env file
Get-Content .env | Select-String -Pattern "MAX_UPLOAD"

# Increase if needed
# Add or update in .env:
MAX_UPLOAD_FILE_SIZE_MB=100
```

**Then rebuild:**
```powershell
docker compose down
docker compose up -d
```

---

## Diagnostic Commands

### Check Container Status

```powershell
# List running containers
docker ps

# Should show both:
# - ollama (running)
# - rag-app (running)
```

### Check Container Logs

```powershell
# All logs
docker compose logs rag-app

# Last 50 lines
docker compose logs --tail=50 rag-app

# Follow in real-time
docker compose logs -f rag-app

# Show errors only
docker compose logs rag-app 2>&1 | Select-String -Pattern "error"
```

### Check API Endpoint Directly

**Using curl or PowerShell:**

```powershell
# Test health endpoint
Invoke-WebRequest -Uri http://localhost:8000/health

# Should return: {"status": "healthy", ...}
```

### Check File System

```powershell
# Check pdfs folder exists in container
docker compose exec rag-app ls -la /app/pdfs

# Check if test file exists
docker compose exec rag-app ls -la /app/pdfs/test.pdf
```

### Check Network

```powershell
# Test if web UI is accessible
Test-NetConnection -ComputerName localhost -Port 8000

# Should show: TcpTestSucceeded : True
```

---

## Full Clean Rebuild

If nothing else works, try a complete clean rebuild:

```powershell
# 1. Stop and remove everything
docker compose down -v

# 2. Remove all Docker cache (optional but thorough)
docker system prune -a
# Type 'y' to confirm

# 3. Rebuild from scratch
docker compose build --no-cache

# 4. Start fresh
docker compose up -d

# 5. Watch startup
docker compose logs -f rag-app

# 6. Wait for "Application startup complete"

# 7. Test upload again
```

---

## Browser-Specific Issues

### Clear Browser Cache

**Chrome/Edge:**
```
Ctrl + Shift + Delete
→ Clear cached images and files
→ Clear
```

**Or hard refresh:**
```
Ctrl + Shift + R
```

### Check Browser Console

**F12 → Console tab**

**Look for:**
- Network errors (red)
- CORS errors
- JavaScript errors

**Common fixes:**
- Hard refresh (Ctrl + Shift + R)
- Clear cache
- Try different browser
- Disable browser extensions

---

## Test with Simple File

**Create test PDF:**

1. Open any text editor
2. Type: "This is a test"
3. Print to PDF
4. Save as: `test.pdf`
5. Try uploading this simple file

**Why:** Complex PDFs might have:
- Invalid characters in filename
- Metadata issues
- Size problems

Simple test file eliminates these variables.

---

## Check Settings

### Verify .env File

```powershell
Get-Content .env
```

**Should have:**
```env
PDF_FOLDER=pdfs
MAX_UPLOAD_FILE_SIZE_MB=50
ALLOWED_FILE_EXTENSIONS=.pdf
```

### Verify docker-compose.yml

```powershell
Get-Content docker-compose.yml | Select-String -Pattern "pdfs"
```

**Should show:**
```yaml
volumes:
  - ./pdfs:/app/pdfs
```

---

## Expected Working Behavior

**Successful upload looks like:**

1. **Click "Upload PDF Files"**
   - File picker opens

2. **Select test.pdf**
   - Upload starts

3. **Progress bar appears**
   - Shows percentage
   - Updates in real-time

4. **Success message:**
   ```
   ✓ Upload successful
   Successfully uploaded 1 file(s) (0.5 MB)
   ```

5. **File appears in pdfs/ folder**
   ```powershell
   dir pdfs\
   # Should show: test.pdf
   ```

6. **"Start Ingestion" button enabled**
   - Can proceed with ingestion

---

## Still Not Working?

### Provide These Details:

1. **Exact error message from browser console** (F12 → Console)

2. **Docker logs showing the error:**
   ```powershell
   docker compose logs --tail=100 rag-app > logs.txt
   ```

3. **Output of these commands:**
   ```powershell
   docker ps
   docker compose config
   dir pdfs\
   ```

4. **What file you're trying to upload:**
   - Filename
   - File size
   - Where you got it from

5. **Whether you rebuilt the container:**
   ```powershell
   docker compose build --no-cache
   ```

### Contact Points:

- GitHub Issues: https://github.com/MoCode98/medical-research-rag/issues
- Include all details above

---

## Quick Checklist

Before asking for help, verify:

- [ ] Transferred updated `api/ingest.py` to Windows
- [ ] Ran `docker compose down`
- [ ] Ran `docker compose build --no-cache`
- [ ] Ran `docker compose up -d`
- [ ] Waited for "Application startup complete" in logs
- [ ] Hard refreshed browser (Ctrl + Shift + R)
- [ ] Tried with simple test.pdf file
- [ ] Checked browser console (F12) for errors
- [ ] Checked Docker logs for errors
- [ ] Docker Desktop is running
- [ ] Both containers are running (`docker ps`)

---

## Version Check

**To verify you have the latest fix:**

```powershell
# Check function signature in api/ingest.py
Get-Content api\ingest.py | Select-String -Pattern "async def upload_pdfs" -Context 0,1

# Should show (NO "request: Request" parameter):
# @router.post("/upload")
# async def upload_pdfs(files: list[UploadFile] = File(...)) -> dict[str, Any]:
```

**Git commit that should be present:**
```
7cd99ad - Simplify upload endpoint - remove unused Request parameter
```

---

## Summary

**Most common cause:** Container not rebuilt after fix

**Most common solution:**
```powershell
docker compose down
docker compose build --no-cache
docker compose up -d
```

**Second most common cause:** Browser cache

**Solution:**
```
Ctrl + Shift + R
```

**If still broken:** Full clean rebuild (see "Full Clean Rebuild" section above)

**Success indicator:** Green banner saying "✓ Upload successful"

Good luck! 🚀
