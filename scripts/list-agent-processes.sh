#!/bin/bash
# scripts/list-agent-processes.sh
# Purpose: Show processes relevant to agent/browser/automation debugging.

echo "Listing agent-related processes..."
echo "PID      PPID     PGID     STAT ELAPSED  %CPU %MEM COMMAND"

ps -Ao pid,ppid,pgid,stat,etime,pcpu,pmem,command | grep -E "Antigravity|Electron|browser_core|Google Chrome for Testing|Chrome|node|npm|pnpm|python|python3|playwright|puppeteer|testdompro|caffeinate" | grep -v grep
