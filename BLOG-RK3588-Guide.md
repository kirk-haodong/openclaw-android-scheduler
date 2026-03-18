

---

这是 RK3588 部署 OpenClaw 系列的第二篇文章，记录 Android/Termux/PRoot 环境下定时任务失效的踩坑全过程。

**系列文章目录：**
- 第一章  [RK3588 部署 OpenClaw 完整记录](https://blog.csdn.net/your_blog_link)
- **第二章  RK3588 OpenClaw 定时任务踩坑与守护进程方案**（本文）
- 第三章  OpenClaw Skill 开发实践（待更新）

**相关资源：**
- 📦 **Skill 仓库**：[openclaw-android-scheduler](https://github.com/kirk-haodong/openclaw-android-scheduler)

---

@[TOC](文章目录)

---

# 前言

在上一篇文章中，我们成功在 RK3588 Android 开发板上部署了 OpenClaw AI 网关，并接入了飞书机器人。然而在实际使用过程中，我遇到了一个棘手的问题：**定时任务无法触发**。

本文详细记录从问题发现、原理分析到最终解决方案的完整过程。涉及 PRoot 容器环境限制、Linux 定时机制差异、Python 守护进程开发等核心知识点。

---

# 一、问题现象：定时任务石沉大海

## 1.1 业务场景

我希望 OpenClaw 能够每天自动推送股票报告：
- **早盘报告**：工作日 9:00 推送
- **收盘报告**：工作日 15:10 推送

## 1.2 尝试方案一：OpenClaw 内置 Cron

根据官方文档，OpenClaw 提供了内置的 cron 功能。我创建了 `/root/.openclaw/cron/jobs.json`：

```json
{
  "version": 1,
  "jobs": [
    {
      "id": "stock-morning-report",
      "name": "股票早盘报告",
      "schedule": {
        "kind": "cron",
        "expr": "0 9 * * 1-5",
        "tz": "Asia/Shanghai"
      },
      "channel": "feishu",
      "to": "oc_xxxxxxxxxx",
      "enabled": true
    }
  ]
}
```

**预期**：工作日 9:00 自动触发，推送报告到飞书群
**实际**：到了 9:00，没有任何消息推送

## 1.3 尝试方案二：系统级 Cron

我尝试在 `/etc/cron.d/` 添加定时任务：

```bash
# /etc/cron.d/openclaw-stock-report
5 9 * * 1-5 root python3 /path/to/report.py
```

**结果**：同样没有执行，没有任何日志

---

# 二、原理分析：为什么定时任务失效

## 2.1 PRoot 环境架构回顾

回顾我们的部署架构：

```
Android OS (RK3588)
  └── Termux 应用
       └── Proot Debian 容器  ← OpenClaw 运行在这里
```

## 2.2 核心问题：容器环境的限制

### 踩坑点 1：OpenClaw 内置 Cron 依赖 Systemd

OpenClaw 的 cron 功能设计运行在标准 Linux 环境，需要 systemd 来管理服务。但在 PRoot 容器中：

```bash
systemctl status cron
# Failed to connect to bus: No such file or directory
```

**根本原因**：PRoot 是用户空间实现的 chroot，没有 PID 1 的 init 系统，systemd 无法运行。

### 踩坑点 2：系统 Cron 服务未运行

标准 Linux 的 cron 服务（crond）同样依赖 init 系统启动：

```bash
service cron status
# cron: unrecognized service

systemctl status cron
# System has not been booted with systemd as init system
```

**结论**：在 PRoot 容器中，传统的 cron 机制完全不可用。

### 踩坑点 3：Heartbeat 机制的不确定性

我尝试使用 OpenClaw 的 Heartbeat 机制，在 `HEARTBEAT.md` 中添加检查脚本。但发现：
- Heartbeat 触发频率由服务端控制
- 不一定能在设定的时间窗口内触发
- 无法满足精确到分钟级的定时需求

## 2.3 环境限制总结

| 定时机制 | 在 PRoot 中的状态 | 原因 |
|:--------:|:----------------:|:-----|
| OpenClaw 内置 cron | ❌ 不可用 | 需要 systemd |
| 系统级 cron (`/etc/cron.d`) | ❌ 不可用 | 无 crond 服务 |
| 标准 crontab | ❌ 不可用 | 缺乏 init 系统 |
| at 命令 | ❌ 不可用 | 依赖 atd 服务 |
| OpenClaw Heartbeat | ⚠️ 不可靠 | 触发频率不确定 |

---

# 三、解决方案：Python 守护进程

## 3.1 架构设计

既然外部定时机制都不可用，那就自己实现一个：

```
┌─────────────────────────────────────────────────────────────┐
│                     Python 守护进程                          │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  • 自主运行，不依赖 systemd/cron                       │  │
│  │  • 每分钟检查一次时间                                   │  │
│  │  • 北京时间（UTC+8）时区处理                            │  │
│  │  • JSON 状态文件防止重复执行                            │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## 3.2 核心实现

### 时区处理（关键！）

RK3588 系统时间是 UTC，但定时任务需要北京时间：

```python
from datetime import datetime, timezone, timedelta

# 必须显式指定北京时间
BEIJING_TZ = timezone(timedelta(hours=8))

def get_beijing_now():
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)
```

**踩坑点 4：时区错误导致任务不触发**

最初使用 `datetime.now()` 获取的是 UTC 时间（北京时间 - 8 小时），导致任务在错误的时间点检查，永远触发不了。

### 时间窗口设计

使用 5 分钟窗口避免重复执行：

```python
def should_run_morning():
    """早盘报告检查 (9:00-9:05)"""
    now = get_beijing_now()
    current_time = now.time()
    # 9:00-9:05 窗口
    return dt_time(9, 0) <= current_time <= dt_time(9, 5)
```

### 状态追踪

防止同一天多次执行：

```python
def check_already_executed(task_id):
    """检查今天是否已执行过"""
    state = load_state()
    today = get_beijing_now().strftime('%Y-%m-%d')
    return state.get(task_id, {}).get('last_executed') == today
```

## 3.3 完整代码

完整实现已封装为 OpenClaw Skill，仓库地址：

📦 **[github.com/kirk-haodong/openclaw-android-scheduler](https://github.com/kirk-haodong/openclaw-android-scheduler)**

使用方法：

```bash
# 1. 复制模板
cp scripts/daemon_template.py /root/.openclaw/workspace/scripts/stock_scheduler.py

# 2. 编辑配置
vim stock_scheduler.py
# 修改 TASKS 字典配置你的任务

# 3. 启动守护进程
python3 stock_scheduler.py start

# 4. 验证
ps aux | grep stock_scheduler | grep -v grep
cat /tmp/stock_scheduler.log
```

---

# 四、调试经验与验证

## 4.1 调试过程记录

### 第一轮测试：17:00 测试任务

**配置**：
```python
"test-1700": {
    "hour": 17,
    "minute": 0,
    "command": "echo 'Test at 17:00'"
}
```

**结果**：没有收到推送

**排查**：
```bash
# 检查系统时间
date
# Wed Mar 18 09:00:00 UTC 2026

# 检查北京时间
TZ=Asia/Shanghai date
# Wed Mar 18 17:00:00 CST 2026
```

**发现**：守护进程使用 `datetime.now()` 获取的是 UTC 9:00，而非北京时间 17:00！

### 第二轮测试：修复时区后

修复代码，强制使用 UTC+8：

```python
BEIJING_TZ = timezone(timedelta(hours=8))
beijing_now = datetime.now(BEIJING_TZ)
```

重新测试，**成功收到推送**！

### 第三轮测试：18:00 验证

为了确保稳定性，再次设置 18:00 测试：

```bash
# 北京时间 18:00
[18:00测试] ✅ 北京时间18:00测试成功！守护进程正常工作
```

**验证通过**！

## 4.2 守护进程管理命令

```bash
# 查看状态
ps aux | grep stock_scheduler | grep -v grep
cat /tmp/stock_scheduler.log

# 重启
python3 stock_scheduler.py restart

# 停止
python3 stock_scheduler.py stop

# 手动测试
python3 stock_scheduler.py once
```

## 4.3 日志样例

```
[2026-03-18 18:04:33 (UTC 10:04:33)] 守护进程启动
[2026-03-18 18:04:33 (UTC 10:04:33)] 当前北京时间: 2026-03-18 18:04:33
[2026-03-18 18:04:33 (UTC 10:04:33)] 当前UTC时间: 2026-03-18 10:04:33
[2026-03-18 09:00:15 (UTC 01:00:15)] 🚀 执行早盘报告...
[2026-03-18 09:00:45 (UTC 01:00:45)] ✅ 早盘报告执行成功
```

---

# 五、踩坑点汇总与解决方案

| 踩坑点 | 现象 | 解决方案 |
|:-----:|:----:|:---------|
| **1. OpenClaw 内置 cron 失效** | 配置了 jobs.json 但任务不触发 | 使用 Python 守护进程替代 |
| **2. 系统 cron 不可用** | /etc/cron.d/ 配置无效 | PRoot 无 crond 服务，用守护进程 |
| **3. Heartbeat 不可靠** | 无法在精确时间触发 | 自主实现每分钟检查 |
| **4. 时区错误** | UTC 时间 vs 北京时间混淆 | 强制使用 `timezone(timedelta(hours=8))` |
| **5. 重复执行** | 同一任务一天内多次触发 | JSON 状态文件记录执行历史 |
| **6. 进程管理** | 如何后台运行/重启/停止 | PID 文件 + 信号处理 |

---

# 六、最佳实践

## 6.1 定时任务配置速查

```python
TASKS = {
    "morning-report": {
        "hour": 9,              # 北京时间 9:00
        "minute": 0,
        "window_minutes": 5,    # 9:00-9:05 窗口
        "days": [0,1,2,3,4],    # 周一到周五
        "command": "python3 /path/to/morning.py"
    },
    "closing-report": {
        "hour": 15,
        "minute": 10,           # 15:10（A股收盘后）
        "window_minutes": 5,
        "days": [0,1,2,3,4],
        "command": "python3 /path/to/closing.py"
    }
}
```

## 6.2 部署检查清单

- [ ] 复制 daemon_template.py 到工作目录
- [ ] 配置 TASKS 字典（注意北京时间）
- [ ] 启动守护进程：`python3 xxx.py start`
- [ ] 验证进程在运行：`ps aux | grep xxx`
- [ ] 查看日志确认无错误：`cat /tmp/xxx.log`
- [ ] 设置开机自启（可选）：添加到 `.bashrc`

## 6.3 相关资源

- **Skill 仓库**：[github.com/kirk-haodong/openclaw-android-scheduler](https://github.com/kirk-haodong/openclaw-android-scheduler)
- **OpenClaw 官方文档**：[docs.openclaw.ai](https://docs.openclaw.ai)
- **Termux 文档**：[termux.dev](https://termux.dev)

---

# 总结

在 RK3588 Android 开发板上部署定时任务，最大的坑在于 **PRoot 容器缺乏 systemd/init 系统**，导致所有传统 cron 机制都不可用。

最终的解决方案是**自主实现 Python 守护进程**：
1. 独立运行，不依赖外部服务
2. 显式处理北京时间（UTC+8）
3. JSON 状态文件防止重复执行
4. PID 文件管理进程生命周期

希望这份踩坑指南能帮助到同样在嵌入式 Android 设备上需要定时任务的开发者。

**系列文章：**
- 第一章：[RK3588 部署 OpenClaw 完整记录](https://blog.csdn.net/your_blog_link)
- **第二章：本文**
- 第三章：OpenClaw Skill 开发实践（待更新）

---

**参考资料：**
- [OpenClaw Android Scheduler](https://github.com/kirk-haodong/openclaw-android-scheduler)
- [OpenClaw Documentation](https://docs.openclaw.ai)
- [Python Daemon Pattern](https://docs.python.org/3/library/multiprocessing.html)

---
