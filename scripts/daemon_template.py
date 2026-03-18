#!/usr/bin/env python3
"""
Android/Termux/PRoot 定时任务守护进程模板
使用 UTC+8 北京时间
"""
import sys
import os
import time
import signal
import json
from datetime import datetime, time as dt_time, timedelta, timezone
from pathlib import Path

# ==================== 配置区域 ====================
# 守护进程名称（用于日志和PID文件）
DAEMON_NAME = "my_daemon"

# 脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 任务配置
# 格式: "任务ID": {"hour": 时, "minute": 分, "window_minutes": 窗口分钟数, "days": [星期列表], "command": "执行的命令"}
# days: 0=周一, 1=周二, ..., 6=周日
TASKS = {
    # 示例任务1：每天早上9:00执行（工作日）
    "morning-task": {
        "hour": 9,
        "minute": 0,
        "window_minutes": 5,  # 9:00-9:05 窗口内执行
        "days": [0, 1, 2, 3, 4],  # 周一到周五
        "command": f"cd {SCRIPT_DIR} && echo 'Morning task executed'"  # 替换为实际命令
    },
    # 示例任务2：每天晚上18:00执行（每天）
    "evening-task": {
        "hour": 18,
        "minute": 0,
        "window_minutes": 5,
        "days": [0, 1, 2, 3, 4, 5, 6],  # 每天
        "command": f"cd {SCRIPT_DIR} && echo 'Evening task executed'"
    }
}

# ==================== 内部实现 ====================
PID_FILE = f"/tmp/{DAEMON_NAME}.pid"
LOG_FILE = f"/tmp/{DAEMON_NAME}.log"
STATE_FILE = os.path.join(SCRIPT_DIR, f"{DAEMON_NAME}_state.json")

# 北京时间时区 (UTC+8)
BEIJING_TZ = timezone(timedelta(hours=8))

def log(msg):
    """记录日志，同时显示北京时间和UTC时间"""
    beijing_now = datetime.now(BEIJING_TZ)
    utc_now = datetime.now(timezone.utc)
    timestamp = f"{beijing_now.strftime('%Y-%m-%d %H:%M:%S')} (UTC {utc_now.strftime('%H:%M:%S')})"
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + "\n")

def get_beijing_now():
    """获取当前北京时间"""
    return datetime.now(BEIJING_TZ)

def load_state():
    """加载执行状态"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_state(state):
    """保存执行状态"""
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def check_already_executed(task_id):
    """检查今天是否已执行过该任务"""
    state = load_state()
    today = get_beijing_now().strftime('%Y-%m-%d')
    task_state = state.get(task_id, {})
    return task_state.get('last_executed') == today and task_state.get('status') == 'success'

def mark_executed(task_id, status='success', message=''):
    """标记任务已执行"""
    state = load_state()
    today = get_beijing_now().strftime('%Y-%m-%d')
    state[task_id] = {
        'last_executed': today,
        'status': status,
        'message': message,
        'timestamp': datetime.now(timezone.utc).isoformat()
    }
    save_state(state)

def should_run_task(task_config):
    """检查任务是否应该执行"""
    now = get_beijing_now()
    current_time = now.time()
    weekday = now.weekday()
    
    # 检查星期
    if weekday not in task_config['days']:
        return False
    
    # 计算时间窗口
    hour = task_config['hour']
    minute = task_config['minute']
    window = task_config.get('window_minutes', 5)
    
    start_time = dt_time(hour, minute)
    end_minute = minute + window
    end_hour = hour
    if end_minute >= 60:
        end_hour += 1
        end_minute -= 60
    end_time = dt_time(end_hour % 24, end_minute)
    
    # 检查是否在窗口内
    return start_time <= current_time <= end_time

def execute_task(task_id, task_config):
    """执行任务"""
    log(f"🚀 执行任务: {task_id}")
    command = task_config['command']
    
    exit_code = os.system(f"{command} >> {LOG_FILE} 2>&1")
    
    if exit_code == 0:
        log(f"✅ 任务 {task_id} 执行成功")
        mark_executed(task_id, 'success', '执行成功')
    else:
        log(f"❌ 任务 {task_id} 执行失败，exit code: {exit_code}")
        mark_executed(task_id, 'failed', f'exit code: {exit_code}')

def main_loop():
    """主循环"""
    log(f"{DAEMON_NAME} 守护进程启动")
    log(f"当前北京时间: {get_beijing_now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"当前UTC时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"配置任务: {list(TASKS.keys())}")
    
    while True:
        beijing_now = get_beijing_now()
        current_time = beijing_now.time()
        
        # 检查每个任务
        for task_id, task_config in TASKS.items():
            if should_run_task(task_config) and not check_already_executed(task_id):
                execute_task(task_id, task_config)
        
        # 每分钟检查一次
        time.sleep(60)

def daemonize():
    """转为守护进程"""
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        log(f"Fork #1 failed: {e}")
        sys.exit(1)
    
    os.chdir("/")
    os.setsid()
    os.umask(0)
    
    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
    except OSError as e:
        log(f"Fork #2 failed: {e}")
        sys.exit(1)
    
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))
    
    sys.stdout.flush()
    sys.stderr.flush()
    
    main_loop()

def start_daemon():
    """启动守护进程"""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                old_pid = f.read().strip()
            if old_pid and os.path.exists(f"/proc/{old_pid}"):
                log(f"守护进程已在运行 (PID: {old_pid})")
                return
        except:
            pass
    
    log("启动守护进程...")
    daemonize()

def stop_daemon():
    """停止守护进程"""
    if not os.path.exists(PID_FILE):
        log("守护进程未运行")
        return
    
    try:
        with open(PID_FILE, 'r') as f:
            pid = int(f.read().strip())
        
        os.kill(pid, signal.SIGTERM)
        os.remove(PID_FILE)
        log(f"守护进程已停止 (PID: {pid})")
    except ProcessLookupError:
        log("进程不存在，清理 PID 文件")
        os.remove(PID_FILE)
    except Exception as e:
        log(f"停止失败: {e}")

def run_once():
    """立即执行一次检查（用于测试）"""
    log("执行单次检查...")
    log(f"北京时间: {get_beijing_now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"UTC时间: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')}")
    
    for task_id, task_config in TASKS.items():
        if should_run_task(task_config):
            if not check_already_executed(task_id):
                log(f"⏰ 任务 {task_id} 在时间窗口内，准备执行...")
                execute_task(task_id, task_config)
            else:
                log(f"⏸️ 任务 {task_id} 今天已执行过")
        else:
            log(f"⏸️ 任务 {task_id} 不在时间窗口")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=f'{DAEMON_NAME} - Android/Termux/PRoot 定时任务守护进程')
    parser.add_argument("command", choices=["start", "stop", "restart", "once"], 
                       default="once", nargs="?",
                       help="start: 启动守护进程, stop: 停止, restart: 重启, once: 单次执行")
    args = parser.parse_args()
    
    if args.command == "start":
        start_daemon()
    elif args.command == "stop":
        stop_daemon()
    elif args.command == "restart":
        stop_daemon()
        start_daemon()
    elif args.command == "once":
        run_once()
