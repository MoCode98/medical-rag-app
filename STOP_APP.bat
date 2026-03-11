@echo off
REM Medical Research RAG - Shutdown Script
REM This script stops the Docker containers

echo.
echo ========================================
echo  Medical Research RAG Pipeline
echo  Stopping Application
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Docker Desktop is not running.
    echo The containers may already be stopped.
    echo.
    pause
    exit /b 0
)

echo Stopping containers...
docker compose stop

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to stop containers!
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Application stopped successfully!
echo ========================================
echo.
echo Your data has been preserved.
echo Run START_APP.bat to start again.
echo.
pause
exit /b 0
