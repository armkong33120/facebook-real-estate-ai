#!/bin/bash
# scripts/run-safe.sh
# Purpose: Run one command safely with timeout and process group cleanup.

set -euo pipefail
set -m # Enable job control for process grouping

TIMEOUT_VAL=${TIMEOUT:-60}
# Join all arguments into a single command string
COMMAND="$*"

if [ -z "$COMMAND" ]; then
    echo "Usage: $0 <command>"
    exit 125
fi

START_TIME=$(date +%s)
echo "--- SAFE RUN START ---"
echo "Timestamp: $(date)"
echo "Command: $COMMAND"
echo "Timeout: $TIMEOUT_VAL seconds"
echo "Parent PID: $$"

# Run command in background (will have its own PGID due to set -m)
# We use eval to allow complex commands
eval "$COMMAND" &
CHILD_PID=$!
PGID=$(ps -o pgid= -p "$CHILD_PID" | tr -d ' ')
echo "Child PID: $CHILD_PID"
echo "Child PGID: $PGID"

# Watchdog in background (Portable macOS fallback)
(
    sleep "$TIMEOUT_VAL"
    if ps -p "$CHILD_PID" > /dev/null; then
        echo "--- TIMEOUT EXCEEDED ($TIMEOUT_VAL s) ---" >&2
        echo "Terminating process group $PGID..." >&2
        # On macOS, kill -TERM -PGID kills the group if PGID is valid
        kill -TERM -"$PGID" 2>/dev/null || kill -TERM "$CHILD_PID" 2>/dev/null
        sleep 3
        if ps -p "$CHILD_PID" > /dev/null; then
            echo "Force killing process group $PGID..." >&2
            kill -KILL -"$PGID" 2>/dev/null || kill -KILL "$CHILD_PID" 2>/dev/null
        fi
    fi
) &
WATCHDOG_PID=$!

# Wait for child
set +e
wait "$CHILD_PID"
EXIT_CODE=$?
set -e

# Clean up watchdog
kill "$WATCHDOG_PID" 2>/dev/null || true

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo "Exit Code: $EXIT_CODE"
echo "Duration: ${DURATION}s"
echo "--- SAFE RUN END ---"

exit "$EXIT_CODE"
