#!/bin/bash
echo "Running info core..."
python info_core_main.py > "/home/info_core/info_core/loggers/logs/info_core_stdout.log" 2>&1 &
