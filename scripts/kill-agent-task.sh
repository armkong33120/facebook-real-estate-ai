#!/bin/bash
# scripts/kill-agent-task.sh
# Purpose: Safely stop only a specific task/process pattern.

PATTERN=${PATTERN:-""}
CONFIRM=${CONFIRM:-0}

if [ -z "$PATTERN" ]; then
    echo "Error: PATTERN environment variable is required."
    exit 1
fi

# Refuse broad dangerous patterns
if [[ "$PATTERN" =~ ^(node|python|chrome|Electron|Antigravity|browser_core|caffeinate|bash|zsh)$ ]]; then
    echo "Error: Pattern '$PATTERN' is too broad and dangerous. Refusing to kill."
    exit 1
fi

echo "Searching for processes matching pattern: $PATTERN"
MATCHES=$(ps -Ao pid,ppid,pgid,stat,etime,pcpu,pmem,command | grep -E "$PATTERN" | grep -v grep | grep -v "kill-agent-task.sh")

if [ -z "$MATCHES" ]; then
    echo "No matching processes found."
    exit 0
fi

echo "Found matching processes:"
echo "PID      PPID     PGID     STAT ELAPSED  %CPU %MEM COMMAND"
echo "$MATCHES"

if [ "$CONFIRM" != "1" ]; then
    echo ""
    echo "DRY RUN MODE. To actually kill, run with: CONFIRM=1 PATTERN=\"$PATTERN\" $0"
    exit 0
fi

echo ""
echo "KILL MODE ENABLED. Proceeding..."

PIDS=$(echo "$MATCHES" | awk '{print $1}')

for PID in $PIDS; do
    echo "Sending SIGTERM to PID $PID..."
    kill -TERM "$PID" 2>/dev/null || true
done

echo "Waiting 3 seconds for graceful exit..."
sleep 3

# Final cleanup
for PID in $PIDS; do
    if ps -p "$PID" > /dev/null; then
        echo "Sending SIGKILL to PID $PID..."
        kill -KILL "$PID" 2>/dev/null || true
    fi
done

echo ""
echo "Remaining matches:"
ps -Ao pid,ppid,pgid,stat,etime,pcpu,pmem,command | grep -E "$PATTERN" | grep -v grep | grep -v "kill-agent-task.sh" || echo "All matched processes terminated."
