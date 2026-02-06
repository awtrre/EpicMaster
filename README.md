<div align="center">

# 🎮 EpicMaster (Pi Edition)

**专为 Raspberry Pi (ARM64) 设计的 Epic Games 自动领取工具**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-ARM64-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![DrissionPage](https://img.shields.io/badge/Core-DrissionPage-green?style=flat-square)](http://g1879.gitee.io/drissionpagedocs/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

[功能特性](#-核心特性) • [安装部署](#-安装与部署) • [配置说明](#-配置说明) • [维护](#-运行与维护)

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
