#!/bin/bash
# scripts/agent-watchdog.sh
# Purpose: Optional watchdog for known task pattern only.

PATTERN=${PATTERN:-""}
MAX_AGE_SECONDS=${MAX_AGE_SECONDS:-300}
CONFIRM=${CONFIRM:-0}

if [ -z "$PATTERN" ]; then
    echo "Error: PATTERN environment variable is required."
    exit 1
fi

# Safety check for broad patterns
if [[ "$PATTERN" =~ ^(node|python|chrome|Electron|Antigravity|browser_core|caffeinate|bash|zsh)$ ]]; then
    echo "Error: Pattern '$PATTERN' is too broad for watchdog. Refusing to monitor."
    exit 1
fi

echo "Watchdog started for pattern: $PATTERN (Max age: $MAX_AGE_SECONDS s)"

while true; do
    # Get matches with elapsed time in seconds (macOS etimes)
    MATCHES=$(ps -Ao pid,etimes,command | grep -E "$PATTERN" | grep -v grep | grep -v "agent-watchdog.sh" || true)
    
    if [ -n "$MATCHES" ]; then
        while read -r line; do
            PID=$(echo "$line" | awk '{print $1}')
            AGE=$(echo "$line" | awk '{print $2}')
            CMD=$(echo "$line" | awk '{$1=""; $2=""; print $0}' | sed 's/^  //')
            
            if [ "$AGE" -gt "$MAX_AGE_SECONDS" ]; then
                echo "[$(date)] Found old process: PID=$PID, AGE=${AGE}s, CMD=$CMD"
                if [ "$CONFIRM" == "1" ]; then
                    echo "[$(date)] TRIGGERING KILL for PID $PID..."
                    CONFIRM=1 PATTERN="^$PID " "$(dirname "$0")/kill-agent-task.sh"
                else
                    echo "[$(date)] DRY RUN: Would kill PID $PID (Run with CONFIRM=1 to kill)"
                fi
            fi
        done <<< "$MATCHES"
    fi
    
    sleep 30
done
