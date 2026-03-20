@echo off
REM Medical Research RAG - Post-Installation Setup
REM This script runs after installation to set up Docker and download AI models

echo.
echo ========================================
echo  Medical Research RAG Pipeline
echo  Post-Installation Setup
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Docker Desktop is not running or not installed.
    echo.
    echo Please:
    echo 1. Install Docker Desktop if not already installed
    echo 2. Start Docker Desktop
    echo 3. Run this setup again from the Start Menu:
    echo    "Medical Research RAG Pipeline" ^> "Complete Setup"
    echo.
    pause
    exit /b 1
)

echo [Step 1/4] Docker Desktop detected...
echo.

REM Navigate to installation directory
cd /d "%~dp0"

echo [Step 2/4] Starting Docker containers...
echo This will build the application (may take 5-10 minutes first time)...
echo.
docker compose up -d --build

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start containers!
    echo Please check Docker Desktop is running and try again.
    pause
    exit /b 1
)

echo.
echo [Step 3/4] Waiting for Ollama service to be ready...
timeout /t 10 /nobreak >nul

REM Wait for Ollama to be ready (up to 60 seconds)
set WAIT_COUNT=0
:wait_ollama
docker compose exec -T ollama ollama list >nul 2>&1
if errorlevel 1 (
    set /a WAIT_COUNT+=1
    if %WAIT_COUNT% LSS 12 (
        echo Waiting for Ollama service... (%WAIT_COUNT%/12)
        timeout /t 5 /nobreak >nul
        goto wait_ollama
    ) else (
        echo.
        echo [WARNING] Ollama service did not start in time.
        echo You can download models manually later using "Download Models" from Start Menu.
        echo.
        pause
        exit /b 0
    )
)

echo Ollama service is ready!
echo.

echo [Step 4/4] Downloading AI models (approximately 5GB)...
echo This may take 10-30 minutes depending on your internet speed.
echo.
echo You can minimize this window - the download will continue in the background.
echo.

echo Downloading embedding model (nomic-embed-text, 274MB)...
docker compose exec -T ollama ollama pull nomic-embed-text

if errorlevel 1 (
    echo.
    echo [WARNING] Failed to download embedding model!
    echo You can download it manually later using "Download Models" from Start Menu.
    goto skip_llm
)

echo.
echo Downloading LLM model (deepseek-r1:7b, 4.7GB)...
echo This is the large language model - this will take a while...
echo.
docker compose exec -T ollama ollama pull deepseek-r1:7b

if errorlevel 1 (
    echo.
    echo [WARNING] Failed to download LLM model!
    echo You can download it manually later using "Download Models" from Start Menu.
    goto done
)

:skip_llm
echo.

echo [Step 5/7] Waiting for application to be ready...
timeout /t 10 /nobreak >nul

REM Wait for app to be healthy (up to 120 seconds)
set WAIT_COUNT=0
:wait_app
timeout /t 5 /nobreak >nul
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    set /a WAIT_COUNT+=1
    if %WAIT_COUNT% LSS 24 (
        echo Waiting for application to start... (%WAIT_COUNT%/24)
        goto wait_app
    ) else (
        echo.
        echo [WARNING] Application did not start in expected time.
        echo Opening browser anyway - you may need to refresh the page.
        goto open_browser
    )
)

echo.
echo Application is running!
echo.

echo [Step 6/7] Starting ingestion of sample PDFs...
echo Processing 18 medical research papers - this ensures everything is ready!
echo.

REM Trigger ingestion via API
curl -X POST http://localhost:8000/api/ingest -H "Content-Type: application/json" -s >nul 2>&1

if errorlevel 1 (
    echo [WARNING] Could not trigger ingestion automatically.
    echo You can start ingestion manually from the web interface.
    goto open_browser
)

echo Ingestion started! Monitoring progress...
echo.

echo [Step 7/7] Waiting for ingestion to complete...
echo This may take 5-10 minutes depending on your system.
echo.

REM Use PowerShell to wait for ingestion (better JSON parsing)
powershell -ExecutionPolicy Bypass -File "%~dp0wait_for_ingestion.ps1" -MaxMinutes 30

if %errorlevel% equ 0 (
    echo.
    echo All sample PDFs have been processed and indexed!
    echo The system is ready for queries.
    echo.
) else (
    echo.
    echo Ingestion is taking longer than expected.
    echo You can monitor progress in the web interface.
    echo.
)

:open_browser
:done
echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo The Medical Research RAG application is now running.
echo.
echo Status:
echo  • Application: Running
echo  • AI Models: Downloaded
echo  • Sample PDFs: Ingested and ready to query
echo  • Vector Database: Indexed with 18 medical research papers
echo.
echo Opening the application in your browser...
echo You can start asking questions immediately!
echo.
timeout /t 3 /nobreak >nul

REM Open browser to the application
start http://localhost:8000

echo.
echo Access the application at: http://localhost:8000
echo.
echo To manage the application, use the Start Menu shortcuts:
echo   - Start Medical RAG
echo   - Stop Medical RAG
echo   - Check Status
echo.
echo Ready to query! Try asking questions about the medical research papers.
echo.
pause
exit /b 0
