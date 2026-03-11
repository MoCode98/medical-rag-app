@echo off
REM Medical Research RAG - Startup Script
REM This script starts the Docker containers and opens the web interface

echo.
echo ========================================
echo  Medical Research RAG Pipeline
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker Desktop is not running!
    echo.
    echo Please start Docker Desktop and try again.
    echo You can find Docker Desktop in your Start Menu.
    echo.
    pause
    exit /b 1
)

echo [1/4] Docker Desktop is running...

REM Check if docker-compose.yml exists
if not exist "docker-compose.yml" (
    echo [ERROR] docker-compose.yml not found!
    echo.
    echo Please make sure you're running this script from the project directory.
    echo.
    pause
    exit /b 1
)

echo [2/4] Starting containers...
docker compose up -d

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start containers!
    echo.
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo [3/4] Containers started successfully!
echo.
echo Waiting for services to be ready...
timeout /t 5 /nobreak >nul

REM Check if models are downloaded
echo [4/4] Checking AI models...
docker compose exec -T ollama ollama list | findstr "nomic-embed-text" >nul 2>&1
if errorlevel 1 (
    echo.
    echo ========================================
    echo  FIRST TIME SETUP REQUIRED
    echo ========================================
    echo.
    echo AI models are not yet downloaded.
    echo This is a one-time download (~5GB).
    echo.
    echo Would you like to download them now?
    echo This will take 10-30 minutes depending on your internet speed.
    echo.
    choice /C YN /M "Download models now"
    if errorlevel 2 goto skip_models
    if errorlevel 1 goto download_models
)

:models_ready
echo.
echo ========================================
echo  APPLICATION IS READY!
echo ========================================
echo.
echo Opening web browser to http://localhost:8000
echo.
echo The application is now running in the background.
echo To stop it, run STOP_APP.bat
echo.
timeout /t 3 /nobreak >nul
start http://localhost:8000
goto end

:download_models
echo.
echo Downloading embedding model (274MB)...
docker compose exec -T ollama ollama pull nomic-embed-text
echo.
echo Downloading LLM model (4.7GB)...
docker compose exec -T ollama ollama pull deepseek-r1:7b
echo.
echo Models downloaded successfully!
goto models_ready

:skip_models
echo.
echo Skipping model download.
echo.
echo NOTE: The application will not work until models are downloaded.
echo Run DOWNLOAD_MODELS.bat later to download them.
echo.
pause
goto end

:end
exit /b 0
