# Agent Process Policy

## Overview
This document outlines the policy for managing terminal commands and child processes executed by the Antigravity agent on this macOS machine. The goal is to prevent stuck processes, resource leaks, and accidental system disruption.

## Core Principles
1. **No Silent Infinite Wait:** Every command should have a timeout.
2. **Process Group Cleanup:** When a task is stopped, all its children (the entire process group) must be cleaned up.
3. **No Dangerous Globals:** Commands like `pkill -9 -f` are forbidden for general use.
4. **Protected Processes:** The following processes must never be killed accidentally:
   - Antigravity / Electron
   - browser_core
   - Google Chrome for Testing
   - node / python (system-wide)
   - caffeinate

## Why Stop/Interrupt May Fail
When you click "Stop" or "Interrupt" in the UI, the agent sends a signal to the top-level shell. However, child processes spawned by that shell (e.g., a long-running python script or a browser instance) may not receive the signal or may ignore it, becoming "orphan" processes that keep running in the background.

## Process Definitions
- **Agent Loop:** The main logic of Antigravity.
- **Terminal Shell:** The bash/zsh process running a command.
- **Child Process:** A process started by the shell.
- **Process Group (PGID):** A collection of related processes. Killing a PGID kills all members.
- **Orphan Process:** A child process whose parent has died but it keeps running.
- **Zombie Process:** A terminated process that still has an entry in the process table.

## Tooling Usage

### 1. Running Commands Safely
Always use `scripts/run-safe.sh` for terminal tasks.
```bash
TIMEOUT=60 scripts/run-safe.sh "your-command here"
```
This script ensures:
- A timeout is enforced.
- The entire process group is terminated on timeout or interruption.
- Detailed logs (start, end, duration, exit code) are provided.

### 2. Listing Agent Processes
Use `scripts/list-agent-processes.sh` to see relevant automation processes.
```bash
scripts/list-agent-processes.sh
```

### 3. Killing a Stuck Task
Use `scripts/kill-agent-task.sh` with a specific pattern.
```bash
# Dry run first
PATTERN="my-stuck-script" scripts/kill-agent-task.sh
# Real kill
CONFIRM=1 PATTERN="my-stuck-script" scripts/kill-agent-task.sh
```

### 4. Automatic Watchdog
For long-running automation, you can start a watchdog.
```bash
PATTERN="my-task" MAX_AGE_SECONDS=600 scripts/agent-watchdog.sh
```

## Approval Policy
- **Read-only commands:** Can be approved for the session.
- **Destructive/Dangerous commands:** Must be approved every time.
- **Never approve always** for commands like `pkill`, `rm -rf`, `sudo`, or system configuration changes.

## Troubleshooting
If the agent is stuck at "Still working..." or "Iteration 1/90":
1. Check `scripts/list-agent-processes.sh`.
2. Look for high CPU or old `ETIME`.
3. Use `scripts/kill-agent-task.sh` to stop the specific runaway process.
4. If the browser bridge is deadlock, restart the agent session.
