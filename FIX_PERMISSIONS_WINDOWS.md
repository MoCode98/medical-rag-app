# Fix: Permission Denied Error on PDF Upload

**Error:** `PermissionError: [Errno 13] Permission denied: 'pdfs/test.pdf'`

**Cause:** Docker container doesn't have write permissions to the `pdfs/` folder

---

## Solution (Windows)

### Option 1: Quick Fix - Recreate pdfs Folder

```powershell
# Navigate to your project
cd "C:\path\to\project"

# Stop containers
docker compose down

# Remove the pdfs folder (backup first if it has important files!)
Remove-Item -Recurse -Force pdfs

# Recreate it
New-Item -ItemType Directory -Path pdfs

# Start containers - Docker will mount with correct permissions
docker compose up -d
```

### Option 2: Fix Permissions on Existing Folder

```powershell
# Navigate to project
cd "C:\path\to\project"

# Give Everyone full control (temporary solution for testing)
icacls pdfs /grant Everyone:F /T

# Restart containers
docker compose restart
```

### Option 3: Use Docker Volume Instead

**Edit docker-compose.yml:**

Change this:
```yaml
volumes:
  - ./pdfs:/app/pdfs
```

To this:
```yaml
volumes:
  - pdfs_data:/app/pdfs

# Add at bottom of file
volumes:
  pdfs_data:
```

Then:
```powershell
docker compose down
docker compose up -d
```

**Note:** With this approach, PDFs are stored in a Docker volume, not directly in your project folder.

---

## Verify the Fix

After applying one of the solutions above:

1. **Test upload:**
   - Open http://localhost:8000
   - Go to Ingest tab
   - Upload a PDF
   - Should succeed!

2. **Check logs:**
   ```powershell
   docker compose logs -f rag-app
   ```
   - Should see: `INFO - Uploaded: test.pdf`
   - No more permission errors

3. **Verify file exists:**
   ```powershell
   # If using mounted folder:
   dir pdfs\

   # If using Docker volume:
   docker compose exec rag-app ls -la /app/pdfs
   ```

---

## Why This Happens

**Windows file permissions + Docker:**
- Docker on Windows uses WSL2 (Windows Subsystem for Linux)
- File permission mapping between Windows and Linux can be tricky
- The `pdfs/` folder might have been created with restrictive permissions
- Docker container runs as a specific user that doesn't have write access

---

## Recommended Solution for Production

**Best practice: Use Docker named volume**

1. **Update docker-compose.yml:**

```yaml
version: '3.8'

services:
  rag-app:
    # ... other config
    volumes:
      - ./src:/app/src
      - ./api:/app/api
      - ./static:/app/static
      - pdfs_data:/app/pdfs      # ← Named volume instead of bind mount
      - ./app.py:/app/app.py
      - data_cache:/app/data
      - vector_db:/app/vector_db

volumes:
  vector_db:
  data_cache:
  ollama_data:
  pdfs_data:                      # ← Add this
```

2. **Rebuild:**

```powershell
docker compose down
docker compose up -d
```

**Benefits:**
- Docker manages permissions automatically
- No Windows/Linux permission conflicts
- Data persists across container rebuilds
- More portable across different systems

**To access PDFs:**
```powershell
# Copy file into volume
docker cp myfile.pdf medical-rag-rag-app-1:/app/pdfs/

# List files in volume
docker compose exec rag-app ls -la /app/pdfs

# Copy file out of volume
docker cp medical-rag-rag-app-1:/app/pdfs/myfile.pdf .
```

---

## Quick Test After Fix

```powershell
# Create simple test
echo "test" > test.txt
# Try to copy to pdfs folder
copy test.txt pdfs\

# If this fails with permission error, the folder permissions are wrong
# If it succeeds, Docker should also be able to write
```

---

## Alternative: Run Container as Root (Not Recommended)

**Only for testing!**

Add to docker-compose.yml under `rag-app` service:

```yaml
rag-app:
  # ... other config
  user: "0:0"  # Run as root
```

Then:
```powershell
docker compose down
docker compose up -d
```

**Why not recommended:**
- Security risk
- Not production-ready
- Better to fix permissions properly

---

## Summary

**Problem:** Container can't write to `pdfs/` folder

**Quick fix:**
```powershell
cd "C:\path\to\project"
docker compose down
Remove-Item -Recurse -Force pdfs
New-Item -ItemType Directory -Path pdfs
docker compose up -d
```

**Best fix:** Use Docker named volume (see "Recommended Solution" above)

**After fix:** Upload should work perfectly! ✅
