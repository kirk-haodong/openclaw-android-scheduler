---
name: openclaw-android-scheduler
description: Schedule recurring tasks for OpenClaw deployed on Android/Termux/PRoot environments. Use when OpenClaw is running on Android (via Termux + PRoot) and the user needs cron-like task scheduling. Automatically detects Android platform and configures daemon-based scheduling since standard cron is unavailable in PRoot containers.
---

# OpenClaw Android Scheduler

Schedule recurring tasks for OpenClaw running on Android devices via Termux + PRoot.

## Problem

When OpenClaw is deployed on Android using Termux + PRoot, standard cron mechanisms don't work:
- OpenClaw built-in cron → Requires systemd (not available in PRoot)
- System cron (`/etc/cron.d`) → No crond service running
- Standard crontab → No init system available

## Solution

Use a Python daemon process that:
- Runs independently as a background process
- Manages its own scheduling logic
- Uses Beijing time (UTC+8) with explicit timezone handling
- Prevents duplicate executions via state tracking

## Platform Detection

This skill automatically detects Android/Termux/PRoot environment:

```bash
# Method 1: Check kernel name for PRoot
uname -a | grep -i "proot"

# Method 2: Check for Termux directory
ls -la /data/data/com.termux 2>/dev/null

# Method 3: Check ANDROID_ROOT
echo $ANDROID_ROOT  # Should be /system on Android

# Method 4: Check for Android properties
getprop ro.product.model 2>/dev/null
```

**If ANY of these return positive results, use this skill for scheduling.**

## Quick Start

### 1. Create Daemon Script

Copy the template to your workspace:

```bash
cp /root/.openclaw/workspace/skills/openclaw-android-scheduler/scripts/daemon_template.py \
   /root/.openclaw/workspace/scripts/my_scheduler.py
```

### 2. Configure Tasks

Edit `my_scheduler.py` and modify the `TASKS` dictionary:

```python
TASKS = {
    "morning-report": {
        "hour": 9,
        "minute": 0,
        "window_minutes": 5,
        "days": [0, 1, 2, 3, 4],  # Mon-Fri
        "command": "python3 /path/to/morning_report.py"
    },
    "evening-report": {
        "hour": 18,
        "minute": 0,
        "window_minutes": 5,
        "days": [0, 1, 2, 3, 4, 5, 6],  # Daily
        "command": "python3 /path/to/evening_report.py"
    }
}
```

### 3. Start Daemon

```bash
cd /root/.openclaw/workspace/scripts
python3 my_scheduler.py start
```

### 4. Verify

```bash
# Check if running
ps aux | grep my_scheduler | grep -v grep

# View logs
cat /tmp/my_scheduler.log
```

## Daemon Management

```bash
# Start
python3 my_scheduler.py start

# Stop
python3 my_scheduler.py stop

# Restart
python3 my_scheduler.py restart

# Run once (for testing)
python3 my_scheduler.py once
```

## Adding New Tasks

1. Edit your daemon script
2. Add entry to `TASKS` dictionary
3. Restart daemon: `python3 my_scheduler.py restart`

## Time Format

All times use **Beijing Time (UTC+8)**:
- `hour`: 0-23
- `minute`: 0-59
- `window_minutes`: Execution window to prevent duplicates (default: 5)
- `days`: List of weekdays (0=Monday, 6=Sunday)

## State Tracking

Execution state is stored in `{daemon_name}_state.json` to prevent duplicate runs.

## Log Files

- Process log: `/tmp/{daemon_name}.log`
- State file: `{daemon_name}_state.json` (in same directory as daemon)

## Troubleshooting

### Daemon not running
```bash
ps aux | grep my_scheduler || python3 my_scheduler.py start
```

### Task not executing
1. Check logs: `tail -50 /tmp/my_scheduler.log`
2. Verify timezone handling in logs
3. Check state file for "already executed" status

### Wrong timezone
The template automatically uses Beijing time (UTC+8). Check logs for:
```
[2026-03-18 18:04:33 (UTC 10:04:33)]
```
First timestamp is Beijing time, second is UTC.

## Template Location

`/root/.openclaw/workspace/skills/openclaw-android-scheduler/scripts/daemon_template.py`

Copy and customize this template for each scheduled task set.

## Use Cases

- **Stock reports**: Daily market open/close reports
- **News summaries**: Scheduled news digest
- **Data sync**: Periodic data synchronization tasks
- **Reminders**: Time-based notification tasks

**Note**: This skill is specifically designed for OpenClaw deployments on Android. For standard Linux deployments, use the built-in OpenClaw cron or system cron instead.
