#!/bin/bash

# Set log directory
LOG_DIR="/home/trade_core/trade_core/loggers/logs"
PID_FILE="/tmp/trade_core_api.pid"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Check if process is already running
if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE")
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "Trade core API is already running with PID $pid"
        exit 1
    fi
fi

echo "Running trade core api with FastAPI server..."
cd api
# uvicorn main:app --host 0.0.0.0 --port 8000 2>&1 | rotatelogs -L "$LOG_DIR/trade_core_api_stdout.log" "$LOG_DIR/trade_core_api_stdout.log.%Y-%m-%d" 604800
uvicorn main:app --host 0.0.0.0 --port 8000

# Save PID for later use
echo $! > "$PID_FILE"

echo "Trade core API started with PID $!"