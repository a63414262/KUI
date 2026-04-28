
# 🚀 KUI - Serverless 极简节点网关控制台

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Architecture](https://img.shields.io/badge/architecture-Serverless-orange.svg)
![Database](https://img.shields.io/badge/database-Cloudflare%20D1-blue.svg)
![Security](https://img.shields.io/badge/security-HMAC--SHA256-red.svg)
![Core](https://img.shields.io/badge/core-Sing--box-black.svg)

KUI 是一个基于 **Cloudflare Pages + D1 数据库** 和 **Sing-box** 构建的极简、轻量级 Serverless 节点管理网关。它彻底抛弃了传统的“面板-数据库-守护进程”笨重架构，实现了**“云端重逻辑，边缘极轻量”**的现代化网络代理管理体验。


## ✨ 核心特性

* ☁️ **纯 D1 驱动的 Serverless 面板**：零成本、免维护。抛弃 KV，拥抱关系型数据库，实现极速查询与完美的数据强一致性。
* 🛡️ **零攻击面 & HMAC 动态军工级鉴权**：
  * **边缘零端口**：VPS 采用纯 Pull 模式，不开放任何 Web 管理端口，免疫一切全网扫描器。
  * **防重放攻击**：抛弃明文 Token，采用前端动态生成 `时间戳 + HMAC-SHA256` 签名，Token 寿命仅 5 分钟，且内存零明文存储。
* 📊 **立体化可观测性 (Observability)**：
  * **7 天流量趋势图**：内置 ECharts，直观展示单机流量走势。
  * **智能休眠轮询**：基于 Page Visibility API，面板切入后台自动休眠，切回瞬间唤醒，极致节省 Cloudflare 请求额度。
  * **Telegram 探针告警**：自带失联巡检 API，节点掉线 3 分钟自动推送 TG 告警。
* 🚀 **前沿协议原生支持**：`VLESS`、`Reality` (自动防封锁)、`Hysteria 2` (自动发签)、`Dokodemo-door` (公网转发 / 内部链式隧道)。

---

## 🛠️ 极速部署指南

KUI 的部署分为三步：**数据库初始化**、**面板部署** 与 **节点接入**。

### 第一步：初始化 Cloudflare D1 数据库

1. 登录 [Cloudflare Dashboard](https://dash.cloudflare.com/)，进入 **Workers & Pages** -> **D1 SQL 数据库**，点击 **创建数据库**（命名为 `kui-db`）。
2. 进入该数据库的 **控制台 (Console)**，**分三次**执行以下 SQL 语句初始化表结构：

**第 1 次执行（节点状态表）：**
```sql
CREATE TABLE IF NOT EXISTS servers (
    ip TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    cpu INTEGER DEFAULT 0,
    mem REAL DEFAULT 0,
    last_report INTEGER DEFAULT 0,
    alert_sent INTEGER DEFAULT 0
);
```
**第 2 次执行（流量聚合表）：**
```sql
CREATE TABLE IF NOT EXISTS traffic_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT NOT NULL,
    delta_bytes INTEGER DEFAULT 0,
    timestamp INTEGER NOT NULL,
    FOREIGN KEY(ip) REFERENCES servers(ip) ON DELETE CASCADE
);
```
**第 3 次执行（性能索引）：**
```sql
CREATE INDEX IF NOT EXISTS idx_traffic_ip_time ON traffic_stats(ip, timestamp);
```

### 第二步：部署云端管理面板

1. **Fork 本仓库** 到你的 GitHub。
2. 在 Cloudflare 中进入 **Workers & Pages** -> **创建** -> **Pages** -> **连接到 Git**，选择你 Fork 的仓库。
3. **设置环境变量 (Settings -> Environment variables)**：
   * `ADMIN_PASSWORD` = `你的高强度登录密码` *(必填)*
   * `TG_BOT_TOKEN` = `你的Telegram机器人Token` *(选填，用于告警)*
   * `TG_CHAT_ID` = `你的TG账号ID` *(选填，用于告警)*
4. **绑定 D1 数据库 (Settings -> Functions -> D1 database bindings)**：
   * 变量名称：`DB`
   * 命名空间：选择你第一步创建的 `kui-db`
5. 点击 **部署**，获取你的控制台专属域名（如 `https://kui-xxx.pages.dev`）。

### 第三步：VPS 一键安全接入

1. 访问你的控制台域名，输入密码登录。
2. 在顶部的 **“接入机器”** 区域输入 VPS 别名与 IP，点击接入。
3. 点击生成的机器卡片底部的 **[终端部署指令]**。
4. SSH 登录到你的 VPS（推荐 Debian 11/12 或 Ubuntu 20.04+），**粘贴并回车**。

*(指令自带前置环境检查，全自动修复缺失组件，闭眼秒装。并且下发的 Token 为加密 Hash，即使 VPS 被黑也无法反推你的面板密码！)*

### 💡 进阶：配置 Telegram 节点失联告警

如果你配置了 TG 环境变量，只需找一个免费的定时任务平台（如 [cron-job.org](https://cron-job.org/)）：
* 创建一个每 **3 分钟** 触发一次的 GET 请求任务。
* 目标 URL：`https://你的面板域名.pages.dev/api/cron`
节点一旦断网超过 3 分钟，你的手机立刻就能收到 Telegram 弹窗报警！

---

## 📂 项目结构

```text
KUI/
├── index.html       # 控制台前端 (Vue3 + Tailwind + ECharts + Web Crypto)
├── functions/
│   └── api/
│       └── [[path]].js # Serverless 后端 API (纯 D1 驱动，HMAC 鉴权拦截)
└── vps/
    ├── kui.sh       # 边缘节点防弹版初始化脚本
    └── agent.py     # 边缘 Python 守护探针 (监控上报 + Sing-box 托管)
```

## ⚠️ 免责声明

本项目仅供网络技术学习、研究与架构测试使用。请遵守当地法律法规，严禁用于任何非法用途。开发者不对使用该工具造成的任何后果负责。
