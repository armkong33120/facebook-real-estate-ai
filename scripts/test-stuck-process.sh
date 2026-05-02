#!/bin/bash
# scripts/test-stuck-process.sh
# Purpose: Simulate a long-running task safely.

echo "[$(date)] Stuck process simulator started. PID: $$"
echo "I will sleep for 999 seconds unless killed."

sleep 999

echo "[$(date)] I woke up! (This should not happen if killed by timeout)"
