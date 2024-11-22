#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Start Redis server with password in the background
echo "Starting local Redis server..."

# Check if REDIS_PASSWORD is set
if [ -z "$REDIS_PASSWORD" ]; then
    echo "ERROR: REDIS_PASSWORD is not set."
    exit 1
fi

# Start Redis server with the specified password
redis-server --requirepass "$REDIS_PASSWORD" --daemonize yes

# Verify that Redis started and requires the password
redis-cli -a "$REDIS_PASSWORD" ping > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "Local Redis server started successfully and requires a password."
else
    echo "Failed to start local Redis server or incorrect password."
    exit 1
fi

# Set log directory
LOG_DIR="/home/trade_core/trade_core/loggers/logs"
PID_FILE="/tmp/trade_core.pid"

# Create log directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Check if process is already running
if [ -f "$PID_FILE" ]; then
    pid=$(cat "$PID_FILE")
    if ps -p "$pid" > /dev/null 2>&1; then
        echo "Trade core is already running with PID $pid"
        exit 1
    fi
fi

echo "Running trade core..."
python trade_core_main.py 2>&1 | rotatelogs -L "$LOG_DIR/trade_core_stdout.log" "$LOG_DIR/trade_core_stdout.log.%Y-%m-%d" 604800

# Save PID for later use
echo $! > "$PID_FILE"

echo "Trade core started with PID $!"