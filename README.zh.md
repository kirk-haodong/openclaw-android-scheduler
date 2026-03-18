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
  为运行在 Android 设备上的 OpenClaw 提供定时任务调度方案（通过 Termux + PRoot）
</p>

---

## ✨ 功能特性

- 📱 **Android 支持**: 专为 Termux + PRoot 环境设计
- ⏰ **类 Cron 调度**: 无需 systemd 或 cron 服务的可靠任务调度
- 🌏 **时区感知**: 使用北京时间（UTC+8），自动处理时区转换
- 🔄 **状态追踪**: 通过 JSON 状态文件防止重复执行
- 🚀 **守护进程模式**: 作为独立后台进程运行
- 🔧 **易于配置**: 使用简单的 Python 字典配置任务

## 🚀 快速开始

### 环境要求

- 已安装 Termux 的 Android 设备
- PRoot 环境（Debian/Ubuntu）
- Python 3.7+
- 部署在 PRoot 容器中的 OpenClaw

### 安装

```bash
# 复制模板
cp scripts/daemon_template.py /path/to/your/workspace/my_scheduler.py

# 编辑配置
vim my_scheduler.py
```

### 使用方法

在 `TASKS` 字典中配置你的任务：

```python
TASKS = {
    "morning-report": {
        "hour": 9,          # 小时（0-23，北京时间）
        "minute": 0,        # 分钟（0-59）
        "window_minutes": 5,  # 执行窗口（5分钟）
        "days": [0, 1, 2, 3, 4],  # 星期（0=周一，6=周日）
        "command": "python3 /path/to/your_script.py"
    }
}
```

启动守护进程：

```bash
python3 my_scheduler.py start
```

## 📁 项目结构

```
openclaw-android-scheduler/
├── README.md              # 英文文档
├── README.zh.md           # 中文文档（本文件）
├── LICENSE                # MIT 许可证
├── SKILL.md               # OpenClaw Skill 文档
├── CHANGELOG.md           # 版本变更记录
├── scripts/               # 脚本模板
│   └── daemon_template.py
└── assets/                # 资源文件
    └── logo.svg
```

## 🛠️ 故障排除

### 守护进程未运行

```bash
# 检查守护进程是否运行
ps aux | grep my_scheduler | grep -v grep

# 重启守护进程
python3 my_scheduler.py restart
```

### 任务未执行

1. 查看日志：`tail -50 /tmp/my_scheduler.log`
2. 检查时区：查看日志中的北京/UTC 时间戳
3. 检查状态文件：`cat my_scheduler_state.json`

### 权限被拒绝

```bash
# 添加执行权限
chmod +x my_scheduler.py
```

## 📄 许可证

[MIT](LICENSE) © kirk-haodong

## 🙏 致谢

- [OpenClaw](https://docs.openclaw.ai) - AI 智能体平台
- [Termux](https://termux.dev/) - Android 终端模拟器
- [PRoot](https://proot-me.github.io/) - chroot 的用户空间实现
