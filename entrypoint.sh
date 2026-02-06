#!/bin/bash
set -e

# 定义清理函数：由内而外，彻底清理环境
cleanup_environment() {
    echo "🧹 [Entrypoint] Cleaning up stale resources..."
    
    # 1. 杀掉所有相关进程
    pkill -9 -f chromium || true
    pkill -9 -f chrome || true
    pkill -9 -f Xvfb || true
    pkill -9 -f x11vnc || true
    pkill -9 -f websockify || true
    
    # 2. 等待进程彻底释放端口 (避免 TIME_WAIT)
    sleep 2

    # 3. 【关键】清理 X11 锁文件 (防止 Xvfb 启动失败)
    # 如果这个文件存在，Xvfb 会以为屏幕 :1 已经被占用了，导致无法启动
    rm -rf /tmp/.X1-lock
    rm -rf /tmp/.X11-unix/X1
    
    # 4. 清理 Chromium 锁文件
    rm -f /app/data/userdata/SingletonLock
    
    echo "✨ [Entrypoint] Cleanup done."
}

# --- 脚本开始 ---

# 1. 无论是不是第一次运行，先清理一遍
cleanup_environment

# 设置屏幕变量
export DISPLAY=:1
export RESOLUTION=1280x720x16

echo "📺 Starting Xvfb..."
# 增加 -ac (禁用访问控制) 提高兼容性
Xvfb :1 -screen 0 $RESOLUTION -ac &
sleep 2

echo "🔌 Starting VNC Server..."
x11vnc -display :1 -nopw -listen localhost -xkb -ncache 10 -ncache_cr -forever &>/dev/null &
sleep 2

echo "🌐 Starting NoVNC (Source Mode)..."
/opt/novnc/utils/websockify/run --web=/opt/novnc 6080 localhost:5900 > /app/data/novnc.log 2>&1 &
sleep 2

echo "🚀 Starting EpicMaster Loop..."
while true; do
    echo "🐍 Running Python script..."
    
    # 运行 Python，如果崩溃打印错误
    python3 src/main.py || echo "⚠️ Python Script crashed"
    
    echo "💤 Waiting 10s before restart..."
    sleep 10
    
    # 循环重启前，再次清理，防止僵尸进程累积
    cleanup_environment
    
    # 重新拉起 Xvfb (因为 cleanup 把它杀掉了)
    # 注意：这里需要判断 Xvfb 是否还活着，没活着才重启
    if ! pgrep -x "Xvfb" > /dev/null; then
        echo "📺 Restarting Xvfb..."
        Xvfb :1 -screen 0 $RESOLUTION -ac &
        sleep 2
    fi
done
