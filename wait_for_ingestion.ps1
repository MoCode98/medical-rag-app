# PowerShell script to wait for ingestion to complete
# Used by POST_INSTALL_SETUP.bat during installation

param(
    [int]$MaxMinutes = 30
)

Write-Host "Waiting for ingestion to complete (max $MaxMinutes minutes)..." -ForegroundColor Yellow
Write-Host ""

$maxAttempts = $MaxMinutes * 6  # Check every 10 seconds
$attempt = 0
$complete = $false

while ($attempt -lt $maxAttempts) {
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/ingest/status" -Method GET -ErrorAction Stop
        
        if ($response.is_running -eq $false -and $response.complete -eq $true) {
            Write-Host ""
            Write-Host "✓ Ingestion complete!" -ForegroundColor Green
            Write-Host "  Files processed: $($response.files_processed)" -ForegroundColor Cyan
            $complete = $true
            exit 0
        }
        
        # Show progress
        $elapsed = [math]::Round($attempt * 10 / 60, 1)
        $filesProcessed = if ($response.files_processed) { $response.files_processed } else { 0 }
        Write-Host "`rIngestion in progress... [$elapsed min] Files: $filesProcessed" -NoNewline -ForegroundColor Cyan
        
    } catch {
        Write-Host "`rChecking ingestion status... ($attempt/$maxAttempts)" -NoNewline -ForegroundColor Gray
    }
    
    Start-Sleep -Seconds 10
    $attempt++
}

if (-not $complete) {
    Write-Host ""
    Write-Host ""
    Write-Host "⚠ Ingestion is taking longer than expected (>$MaxMinutes minutes)" -ForegroundColor Yellow
    Write-Host "  You can monitor progress in the web interface." -ForegroundColor Yellow
    exit 1
}
