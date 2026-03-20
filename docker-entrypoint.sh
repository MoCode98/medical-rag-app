#!/bin/bash
# Docker entrypoint script
# Ensures proper permissions on mounted volumes before starting the application

set -e

echo "Checking volume permissions..."

# Ensure directories exist and are writable
# This is especially important for Windows hosts where permissions can be tricky
for dir in /app/pdfs /app/vector_db /app/data /app/logs; do
    if [ -d "$dir" ]; then
        # Check if directory is writable
        if [ ! -w "$dir" ]; then
            echo "WARNING: $dir is not writable, attempting to fix..."
            # Try to make it writable (will only work if we have permissions)
            chmod 777 "$dir" 2>/dev/null || echo "Could not change permissions for $dir"
        else
            echo "✓ $dir is writable"
        fi
    else
        echo "Creating $dir..."
        mkdir -p "$dir"
        chmod 777 "$dir"
    fi
done

# Test write access to pdfs folder specifically
if touch /app/pdfs/.write_test 2>/dev/null; then
    rm /app/pdfs/.write_test
    echo "✓ pdfs folder write test passed"
else
    echo "ERROR: Cannot write to /app/pdfs folder"
    echo "This may cause PDF upload failures"
fi

echo "Starting application..."

# Execute the main command (python app.py)
exec "$@"
