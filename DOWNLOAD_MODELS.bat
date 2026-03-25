@echo off
REM Medical Research RAG - Model Download Script
REM This script downloads the AI models (one-time setup, ~1.2GB)

echo.
echo ========================================
echo  Medical Research RAG Pipeline
echo  AI Model Download
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop is not running!
    echo.
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Check if containers are running
docker compose ps | findstr "ollama" | findstr "Up" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Containers are not running!
    echo.
    echo Please run START_APP.bat first to start the containers.
    pause
    exit /b 1
)

echo This will download approximately 1.2GB of data.
echo It may take 3-10 minutes depending on your internet speed.
echo.
choice /C YN /M "Continue with download"
if errorlevel 2 goto cancelled
if errorlevel 1 goto download

:download
echo.
echo [1/2] Downloading embedding model (nomic-embed-text, 274MB)...
echo.
docker compose exec -T ollama ollama pull nomic-embed-text

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to download embedding model!
    pause
    exit /b 1
)

echo.
echo [2/2] Downloading LLM model (deepseek-r1:1.5b, 900MB)...
echo This is much faster than larger models!
echo.
docker compose exec -T ollama ollama pull deepseek-r1:1.5b

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to download LLM model!
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Models downloaded successfully!
echo ========================================
echo.
echo You can now use the application at:
echo http://localhost:8000
echo.
pause
exit /b 0

:cancelled
echo.
echo Download cancelled.
echo.
pause
exit /b 0
