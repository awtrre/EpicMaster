<div align="center">

# 🎮 EpicMaster (Pi Edition)

**专为 Raspberry Pi (ARM64) 设计的 Epic Games 自动领取工具**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-ARM64-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![DrissionPage](https://img.shields.io/badge/Core-DrissionPage-green?style=flat-square)](http://g1879.gitee.io/drissionpagedocs/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

[核心特性](#-核心特性) • [安装部署](#-安装与部署) • [配置说明](#-配置说明) • [运行与维护](#-运行与维护)

</div>

---

## 📖 项目简介

**EpicMaster** 摒弃了臃肿的 Selenium/Playwright，采用 **DrissionPage** 直接通过 CDP 协议控制系统级 Chromium。它专为 **Raspberry Pi** 这种低功耗设备优化，能够有效规避 Cloudflare Turnstile 等高难度验证，实现全自动领取的“零干预”体验。

## ✨ 核心特性

| 特性 | 说明 |
| :--- | :--- |
| **🛡️ 底层隐蔽** | 注入 Windows/NVIDIA 显卡指纹，伪装成桌面环境，拒绝被识别为 Headless 机器人。 |
| **🧠 智能过盾** | 自动识别 Cloudflare/Arkose，采用**拟人化键鼠轨迹**与**键盘盲打**策略突破验证。 |
| **🐋 Docker 隔离** | 基于 `appuser` (非 Root) 运行，支持严格的 **HTTP 代理隔离**，不污染宿主机网络。 |
| **👁️ 可视化监控** | 暴露 `6080` 端口 (NoVNC)，允许在极少数卡顿时进行人工远程介入。 |
| **♻️ 自动守护** | 内置内存看门狗 (Keep-Alive)，浏览器崩溃或 OOM 时自动重启会话。 |

---

## 📂 目录结构

```text
EpicMaster/
├── data/                   # [持久化] 运行数据挂载点
│   ├── logs/               # 运行日志 (按周轮转)
│   ├── userdata/           # 浏览器 Cookies 与缓存
│   └── screenshots/        # 调试截图
├── src/                    # 源代码
│   ├── core/               # 核心逻辑 (Browser, Auth, Claimer)
│   └── fingerprints.json   # 伪造指纹库
├── Dockerfile              # ARM64 构建文件
└── .env                    # 配置文件
```

---

## 🛠️ 安装与部署

由于树莓派 (ARM64) 的特殊性，建议直接使用 Docker 部署，避免复杂的依赖问题。

### 1. 克隆项目
```bash
git clone [https://github.com/awtrre/EpicMaster.git](https://github.com/awtrre/EpicMaster.git)
cd EpicMaster
```

### 2. 构建镜像
构建过程会拉取系统级 Chromium，耗时约 3-5 分钟，请耐心等待。
```bash
# 1. 赋予脚本执行权限
chmod +x entrypoint.sh

# 2. 开始构建
docker build -t epic-master:v1 .
```

### 3. 启动容器
```bash
docker run -d \
  --name epic-bot \
  --restart unless-stopped \
  -p 6080:6080 \
  -v $(pwd)/data:/app/data \
  --env-file .env \
  --shm-size=1gb \
  epic-master:v1
```

> **⚠️ 关键参数说明**
> * `--shm-size=1gb`: **必须添加**。Chromium 在树莓派上极易因共享内存不足而崩溃 (Page Crash)，1GB 是稳定运行的最小值。
> * `-v .../data`: 挂载目录，确保重启容器后 Cookies 和日志不丢失。

---

## ⚙️ 配置说明

请在项目根目录新建 `.env` 文件，参照下表填写：

| 变量名 | 必填 | 默认值 | 说明 / 示例 |
| :--- | :---: | :---: | :--- |
| `EPIC_EMAIL` | ✅ | - | 你的 Epic 登录邮箱 |
| `EPIC_PASSWORD` | ✅ | - | 你的 Epic 登录密码 |
| `PROXY_URL` | ⚠️ | 无 | **强烈建议配置**。格式：`http://192.168.1.X:7890`<br>若不配置，在国内网络环境下极大概率无法加载验证盾。 |
| `HEADLESS` | ❌ | `True` | `True`: 无头模式 (生产环境)<br>`False`: 调试模式 (开启浏览器界面) |

> **📝 提示**：程序会自动忽略系统环境变量（如 `http_proxy`），**只认** `.env` 里的 `PROXY_URL`，以确保 Docker 容器内的网络隔离性。

---

## 🖥️ 运行与维护

### 📊 查看状态
程序内置了调度器，启动后会立即执行一次检测，随后进入静默等待模式（每天随机时间唤醒）。

```bash
# 查看实时滚动日志
docker logs -f epic-bot

# 或查看详细的历史日志文件
tail -f data/logs/epicmaster.log
```

### 🎮 手动介入 (NoVNC)
如果日志提示 `Waiting for manual login` 或卡在复杂的图形验证码上：

1.  **访问地址**: 浏览器打开 `http://<树莓派IP>:6080`
2.  **操作**: 你会看到浏览器画面，直接用鼠标点击解决验证。
3.  **结果**: 解决后程序会自动检测通过，并保存 Cookies，下次即可自动登录。

### 🚑 常见问题

| 现象 | 原因 | 解决方案 |
| :--- | :--- | :--- |
| **Browser is dead** | 树莓派内存不足，进程被杀 | 无需操作。内置看门狗 (Keep-Alive) 会在 1 分钟内自动重启浏览器。 |
| **Cloudflare Loop** | IP 质量过低或指纹失效 | 1. 更换代理节点<br>2. 通过 NoVNC 手动点击一次验证框。 |
| **Permission denied** | Docker 挂载权限问题 | 执行 `chown -R 1000:1000 data/` 修正权限。 |

---

## ⚖️ 免责声明

> 1. 本项目仅供 **Python 自动化技术研究** 与 **编程学习** 使用。
> 2. 请勿将本项目用于商业用途、批量注册或任何违反 Epic Games 服务条款的行为。
> 3. 使用本工具产生的任何后果（包括但不限于账号封禁、数据丢失）由使用者 **自行承担**。
