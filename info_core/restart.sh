#!/bin/bash

# Get directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICE_NAME="info_core_main.py"

echo "Restarting $SERVICE_NAME..."

# Run stop script
"$SCRIPT_DIR/stop.sh"

# Wait for processes to fully stop
sleep 2

# Start new instance
cd "$SCRIPT_DIR"
python "$SERVICE_NAME" > "$SCRIPT_DIR/loggers/logs/info_core_stdout.log" 2>&1 &

echo "Started new $SERVICE_NAME process"