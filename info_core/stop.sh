#!/bin/bash

SERVICE_NAME="info_core_main.py"
KEYWORD="python"

echo "Stopping $SERVICE_NAME and all child processes..."

# Function to get all child PIDs
get_child_pids() {
    local parent_pid="$1"
    local child_pids=$(pgrep -P "$parent_pid")
    echo "$parent_pid $child_pids"
    
    for pid in $child_pids; do
        get_child_pids "$pid"
    done
}

# Get parent PID
parent_pid=$(ps -ef | grep "$SERVICE_NAME" | grep "$KEYWORD" | grep -v grep | awk '{print $2}')

if [ -z "$parent_pid" ]; then
    echo "No $SERVICE_NAME process found."
    exit 0
fi

echo "Found parent process: $parent_pid"

# Get all child PIDs
all_pids=$(get_child_pids "$parent_pid" | tr ' ' '\n' | sort -u)

echo "Killing processes: $all_pids"

# Kill all processes
for pid in $all_pids; do
    kill -9 "$pid" 2>/dev/null
done

# Verify all processes are killed
sleep 2
remaining_pids=$(ps -ef | grep "$SERVICE_NAME" | grep "$KEYWORD" | grep -v grep | awk '{print $2}')

if [ -n "$remaining_pids" ]; then
    echo "Some processes still running. Force killing again..."
    pkill -9 -f "$SERVICE_NAME"
fi

echo "All processes related to $SERVICE_NAME have been terminated."