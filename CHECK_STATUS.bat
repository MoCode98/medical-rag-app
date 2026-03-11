@echo off
REM Medical Research RAG - Status Check Script
REM This script shows the current status of the application

echo.
echo ========================================
echo  Medical Research RAG Pipeline
echo  System Status
echo ========================================
echo.

REM Check if Docker is running
echo [1/4] Checking Docker Desktop...
docker info >nul 2>&1
if errorlevel 1 (
    echo      Status: NOT RUNNING
    echo.
    echo      Please start Docker Desktop.
    echo.
    pause
    exit /b 1
) else (
    echo      Status: RUNNING
)

echo.
echo [2/4] Checking Containers...
docker compose ps
echo.

echo [3/4] Checking AI Models...
docker compose exec -T ollama ollama list 2>nul
if errorlevel 1 (
    echo      [WARNING] Could not check models. Are containers running?
)

echo.
echo [4/4] Checking Web Interface...
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo      Status: NOT ACCESSIBLE
    echo      The web interface is not responding at http://localhost:8000
) else (
    echo      Status: ACCESSIBLE
    echo      Web interface is running at http://localhost:8000
)

echo.
echo ========================================
echo  Status check complete
echo ========================================
echo.
pause
exit /b 0
