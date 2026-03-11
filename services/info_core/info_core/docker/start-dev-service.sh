#!/bin/bash
# Start Redis server in the background
echo "Starting local Redis server..."
redis-server --daemonize yes
 
# Verify that Redis started
redis-cli ping
if [ $? -eq 0 ]; then
    echo "Local Redis server started successfully."
else
    echo "Failed to start local Redis server."
    exit 1
fi

# Set log directory
LOG_DIR="/home/info_core/info_core/loggers/logs"
PID_FILE="/tmp/info_core.pid"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Check if process is already running
if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE")
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "Info core is already running with PID $pid"
        exit 1
    fi
fi

echo "Running info core..."
python info_core_main.py 2>&1 | rotatelogs -L "$LOG_DIR/info_core_stdout.log" "$LOG_DIR/info_core_stdout.log.%Y-%m-%d" 604800

# Save PID for later use
echo $! > "$PID_FILE"

echo "Info core started with PID $!"
