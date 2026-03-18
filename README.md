<p align="center">
  <img src="https://raw.githubusercontent.com/kirk-haodong/openclaw-android-scheduler/main/assets/logo.svg" alt="OpenClaw Android Scheduler" width="180">
</p>

<h1 align="center">OpenClaw Android Scheduler</h1>

<p align="center">
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.7+-blue.svg" alt="Python 3.7+"></a>
  <a href="https://github.com/kirk-haodong/openclaw-android-scheduler/blob/master/LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License"></a>
  <a href="https://github.com/kirk-haodong/openclaw-android-scheduler/stargazers"><img src="https://img.shields.io/github/stars/kirk-haodong/openclaw-android-scheduler.svg?style=social" alt="GitHub stars"></a>
</p>

<p align="center">
  <a href="README.md">English</a> •
  <a href="README.zh.md">中文</a>
</p>

<p align="center">
  Schedule recurring tasks for OpenClaw running on Android devices via Termux + PRoot
</p>

---

## ✨ Features

- 📱 **Android Support**: Specifically designed for Termux + PRoot environments
- ⏰ **Cron-like Scheduling**: Reliable task scheduling without systemd or cron services
- 🌏 **Timezone Aware**: Uses Beijing Time (UTC+8) with automatic handling
- 🔄 **State Tracking**: Prevents duplicate executions via JSON state files
- 🚀 **Daemon Mode**: Runs as independent background process
- 🔧 **Easy Configuration**: Simple Python dictionary for task setup

## 🚀 Quick Start

### Prerequisites

- Android device with Termux installed
- PRoot environment with Debian/Ubuntu
- Python 3.7+
- OpenClaw deployed in PRoot container

### Installation

```bash
# Copy the template
cp scripts/daemon_template.py /path/to/your/workspace/my_scheduler.py

# Edit configuration
vim my_scheduler.py
```

### Usage

Configure your tasks in the `TASKS` dictionary:

```python
TASKS = {
    "morning-report": {
        "hour": 9,
        "minute": 0,
        "window_minutes": 5,
        "days": [0, 1, 2, 3, 4],  # Monday to Friday
        "command": "python3 /path/to/your_script.py"
    }
}
```

Start the daemon:

```bash
python3 my_scheduler.py start
```

## 📁 Project Structure

```
openclaw-android-scheduler/
├── README.md              # This file (English)
├── README.zh.md           # 中文文档
├── LICENSE                # MIT License
├── SKILL.md               # OpenClaw Skill documentation
├── CHANGELOG.md           # Version changelog
├── scripts/               # Script templates
│   └── daemon_template.py
└── assets/                # Assets
    └── logo.svg
```

## 🛠️ Troubleshooting

### Daemon not running

```bash
# Check if daemon is running
ps aux | grep my_scheduler | grep -v grep

# Restart daemon
python3 my_scheduler.py restart
```

### Task not executing

1. Check logs: `tail -50 /tmp/my_scheduler.log`
2. Verify timezone: Look for Beijing/UTC timestamps in logs
3. Check state file: `cat my_scheduler_state.json`

### Permission denied

```bash
# Make script executable
chmod +x my_scheduler.py
```

## 📄 License

[MIT](LICENSE) © kirk-haodong

## 🙏 Acknowledgments

- [OpenClaw](https://docs.openclaw.ai) - The AI agent platform
- [Termux](https://termux.dev/) - Android terminal emulator
- [PRoot](https://proot-me.github.io/) - User-space implementation of chroot
