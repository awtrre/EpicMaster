EpicMaster (Raspberry Pi Edition)
EpicMaster 是一个专为 Raspberry Pi (ARM64) 架构设计的自动化工具，用于自动领取 Epic Games Store 的每周免费游戏。

该项目放弃了传统的 Selenium 或 Playwright，转而采用 DrissionPage 直接控制系统级 Chromium 浏览器。结合 CDP 协议注入和拟人化操作算法，它能够有效规避 Cloudflare Turnstile 等验证系统的检测。

核心特性
底层隐蔽性 基于 DrissionPage 构建，不依赖 WebDriver，降低了被反爬虫系统识别的风险。程序会在启动时通过 CDP 协议注入 Windows 和 NVIDIA 显卡的 WebGL 指纹，防止被识别为 Linux 环境下的无头浏览器。

智能验证处理 内置 ShieldBuster 模块，能够识别 Cloudflare Turnstile、hCaptcha 和 ArkoseLabs 验证。针对高难度验证，采用键盘模拟（Tab + Enter）和非线性鼠标轨迹策略进行尝试。

守护进程模式 程序设计为长期运行的后台服务。内置 APScheduler 调度器，每天在随机时间窗口执行任务。包含看门狗机制（Keep-Alive），如果浏览器因树莓派内存不足而崩溃，会自动重启会话。

Docker 隔离环境 使用非 Root 用户 (appuser) 运行，确保系统安全。支持严格的 HTTP 代理隔离，程序会忽略系统环境变量，仅使用配置文件中指定的代理地址。

可视化监控 虽然主要以无头模式运行，但容器暴露了 6080 端口（NoVNC）。在遇到无法自动解决的验证码时，用户可以通过浏览器访问该端口进行人工干预。

目录结构
Plaintext
EpicMaster/
├── data/                  # 持久化数据目录
│   ├── logs/              # 运行日志
│   ├── userdata/          # 浏览器缓存与 Cookies
│   └── screenshots/       # 调试与报错截图
├── src/
│   ├── config.py          # 环境变量与路径配置
│   ├── main.py            # 程序入口与任务调度
│   ├── fingerprints.json  # 伪造的指纹数据
│   └── core/              # 核心逻辑模块
├── Dockerfile             # 构建文件
└── requirements.txt       # Python 依赖
环境要求
硬件：Raspberry Pi 4B 或更高版本（建议 4GB+ 内存）

系统：Raspberry Pi OS (64-bit)

软件：Docker, Git

安装与部署
1. 克隆代码仓库
Bash
git clone https://github.com/你的用户名/EpicMaster.git
cd EpicMaster
2. 配置环境变量
在项目根目录下创建 .env 文件：

Bash
nano .env
填入以下配置信息。请注意，PROXY_URL 对于国内网络环境通常是必须的。

Ini, TOML
EPIC_EMAIL=your_email@example.com
EPIC_PASSWORD=your_password

# 代理地址 (例如局域网内的代理服务器)
PROXY_URL=http://192.168.1.X:7890

# 调试模式开关 (False 为开启浏览器界面，True 为无头模式)
# 在 Docker 中运行时通常保持默认即可
HEADLESS=True
3. 构建 Docker 镜像
由于树莓派架构特殊，构建过程需要基于系统自带的 Chromium。

Bash
chmod +x entrypoint.sh
docker build -t epic-master:v1 .
4. 启动容器
启动时需要挂载 data 目录以保存 Cookies 和日志，并设置 shm-size 以防止 Chromium 崩溃。

Bash
docker run -d \
  --name epic-bot \
  --restart unless-stopped \
  -p 6080:6080 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  --shm-size=1gb \
  epic-master:v1
维护说明
查看运行状态
可以通过查看容器日志来确认程序是否正常运行：

Bash
docker logs -f epic-bot
或者查看详细的应用日志文件：

Bash
tail -f data/logs/epicmaster.log
手动介入 (NoVNC)
如果日志提示 "Waiting for manual login" 或一直卡在验证环节，可以通过浏览器访问树莓派的 IP 地址进行手动操作：

地址：http://树莓派IP:6080

常见问题
关于浏览器崩溃：树莓派内存资源有限，Chromium 可能会被系统 OOM Killer 杀掉。程序的 ensure_browser_alive 函数会自动检测并重启浏览器，通常无需人工处理。

关于代理：程序实现了严格的代理检查。如果 .env 中的 PROXY_URL 未设置或为空，程序将强制直连，并忽略容器内的系统代理设置。

免责声明
本项目仅供 Python 自动化技术研究与学习使用。请勿用于商业用途。使用本工具产生的任何后果由使用者自行承担。
