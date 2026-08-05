# AI Personal Agent

> 基于 FastAPI + React 的全栈 AI 智能个人网站 — 简历问答 + 联网搜索 + 智能路由

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5-3178C6?logo=typescript)](https://www.typescriptlang.org)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-06B6D4?logo=tailwindcss)](https://tailwindcss.com)
[![DeepSeek](https://img.shields.io/badge/LLM-DeepSeek--v4--pro-6366f1)](https://deepseek.com)
[![ChromaDB](https://img.shields.io/badge/VectorDB-ChromaDB-f59e0b)](https://www.trychroma.com)
[![License](https://img.shields.io/badge/License-MIT-green)](./LICENSE)

---

## 📖 项目简介

AI Personal Agent 是一个智能个人网站，核心是一个**统一 Agent**，能自动判断用户问题类型并选择最佳处理方式：

- **简历/知识库问题** → 三层 RAG 检索（FAQ → 元数据 → 文档） → LLM 生成回答
- **其他问题** → SearXNG 联网搜索 → LLM 综合分析
- **搜索不可用** → LLM 直接回答（兜底）

通过 **Cloudflare Tunnel** 实现一键公网访问，无需服务器、无需域名备案。

---

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────┐
│                   前端 (React)                │
│    TypeScript + Vite + Tailwind CSS          │
│    SSE 流式接收 + Markdown 渲染 + 打字动画     │
└──────────────────┬──────────────────────────┘
                   │ POST /api/chat (SSE)
┌──────────────────▼──────────────────────────┐
│              后端 (FastAPI)                   │
│  ┌───────────────────────────────────┐      │
│  │        统一 Agent 路由              │      │
│  │  FAQ 相似度 ≥ 0.35 → 简历问答       │      │
│  │  非FAQ 相似度 ≥ 0.50 → 简历问答     │      │
│  │  相似度不足 → 联网搜索              │      │
│  └───────────────────────────────────┘      │
│  ┌────────────┐  ┌──────────────────┐      │
│  │  RAG 模块   │  │    搜索模块        │      │
│  │ FAQ 优先    │  │  SearXNG (主)     │      │
│  │ 元数据查询  │  │  DuckDuckGo (备)  │      │
│  │ 文档检索    │  │  LLM 直接 (兜底)  │      │
│  │ ChromaDB   │  └──────────────────┘      │
│  └────────────┘                             │
│  ┌──────────────────────────────────┐      │
│  │  Cloudflare Tunnel (公网穿透)      │      │
│  └──────────────────────────────────┘      │
└─────────────────────────────────────────────┘
```

---

## 📁 项目结构

```
p agent/
│
├── backend/                         # 🔧 后端 (Python FastAPI)
│   ├── main.py                      #    FastAPI 入口，路由定义 + 生命周期管理
│   ├── config.py                    #    配置中心 (API Key / 路径 / RAG 参数)
│   ├── requirements.txt             #    Python 依赖清单
│   ├── agents/                      #    🤖 Agent 层 — 智能对话处理
│   │   ├── unified_agent.py         #       统一路由：自动判断问题类型
│   │   ├── resume_agent.py          #       简历 Agent：RAG 检索 + LLM 生成
│   │   └── search_agent.py          #       搜索 Agent：三级回退搜索策略
│   ├── rag/                         #    📚 RAG 管道 — 文档加载/分块/嵌入/检索
│   │   ├── loader.py                #       文档加载 + Markdown 感知分块 + FAQ/Metadata
│   │   ├── embeddings.py            #       sentence-transformers 文本嵌入 (384维)
│   │   └── vector_store.py          #       ChromaDB 向量存储 + 变更检测自动重建
│   ├── services/                    #    ⚙️ 服务层 — LLM 客户端 + SSE 格式
│   │   ├── llm.py                   #       DeepSeek 流式客户端 (OpenAI 兼容)
│   │   └── sse.py                   #       SSE 事件格式化工具
│   └── utils/                       #    🛠️ 工具层
│       └── cloudflare_tunnel.py     #       Cloudflare 内网穿透管理
│
├── frontend/                        # 🎨 前端 (React TypeScript)
│   ├── package.json                 #    Node 依赖配置
│   ├── vite.config.ts               #    Vite 构建配置 (含 API 代理)
│   ├── tailwind.config.js           #    Tailwind CSS 自定义主题
│   ├── index.html                   #    HTML 入口 (lang=zh-CN)
│   └── src/
│       ├── App.tsx                  #    根组件：布局编排 + 健康检查
│       ├── main.tsx                 #    React 入口
│       ├── index.css                #    全局样式 + Prose 排版 + 滚动条
│       ├── api/
│       │   └── chat.ts              #    SSE 流式客户端 + 配置获取
│       ├── hooks/
│       │   ├── useChat.ts           #    聊天状态机 (对话/消息/流式/取消)
│       │   └── useTheme.ts          #    主题管理 (预留暗色模式)
│       ├── types/
│       │   └── index.ts             #    TypeScript 类型定义
│       └── components/
│           ├── chat/                # 💬 聊天核心组件
│           │   ├── ChatWindow.tsx   #       消息列表 + 自动滚动
│           │   ├── MessageBubble.tsx #      消息气泡 (Markdown 渲染)
│           │   ├── StreamingMessage.tsx #   流式消息 (打字动画)
│           │   ├── WelcomeScreen.tsx #      欢迎页 (功能卡片 + 建议问题)
│           │   ├── InputBox.tsx     #       输入框 (模式切换 + 发送/停止)
│           │   ├── CodeBlock.tsx    #       代码块 (语法高亮 + 一键复制)
│           │   └── StatusBar.tsx    #       状态栏 (连接状态 + Agent 模式)
│           ├── layout/              # 📐 布局组件
│           │   ├── Sidebar.tsx      #       侧边栏 (对话历史 + PDF 下载)
│           │   └── Header.tsx       #       顶栏 (标题 + 新建对话)
│           ├── agent/               # 🤖 Agent 面板
│           │   └── ContextPanel.tsx #       上下文面板 (预留)
│           └── common/              # 🧩 通用组件
│               ├── Button.tsx       #       按钮 (4 种变体 + 3 种尺寸)
│               └── Card.tsx         #       卡片容器
│
├── markdown/                        # 📝 知识库 (三层 RAG 数据源)
│   ├── resume_metadata.json         #    结构化元数据 (教育/技能/项目) + 7条FAQ
│   └── *.md                         #    Markdown 简历原文
│
├── pdf/                             # 📄 简历 PDF (供下载)
│   └── *.pdf                        #    个人简历 PDF 文件
│
├── searxng/                         # 🔍 SearXNG 搜索引擎 (Docker)
│   ├── docker-compose.yml           #    Docker 编排配置
│   ├── settings.yml                 #    搜索引擎配置 (Bing/Baidu/Google/Wikipedia)
│   └── limiter.toml                 #    限流器配置 (已关闭)
│
├── docs/                            # 📖 项目文档
│   ├── 项目复盘总结.md               #    v1.0 原始复盘总结 (2026-07-14)
│   └── 项目总结_v2.md               #    v2.0 最新技术文档 (2026-07-21) ⭐
│
├── .env.example                     # 📋 环境变量模板
├── .gitignore                       # 🙈 Git 忽略规则
├── start.bat                        # 🚀 Windows 一键启动脚本
├── CLAUDE.md                        # 🤖 Claude Code 项目指引
└── README.md                        # 📘 本文件
```

---

## ✨ 核心功能

### 🧠 智能 Agent 路由

| 问题类型 | 判断逻辑 | 处理方式 |
|---------|---------|---------|
| 简历 FAQ 匹配 | FAQ 相似度 ≥ 0.35 | 直接返回预写答案 |
| 简历知识库问题 | 非 FAQ 相似度 ≥ 0.50 | RAG 检索 → LLM 生成 |
| 通用问题 | 相似度低于阈值 | SearXNG 搜索 → LLM 分析 |
| 搜索不可用 | 所有搜索源失败 | LLM 直接回答 |

### 📚 三层 RAG 知识库

| 层级 | 数据来源 | 特点 |
|------|---------|------|
| **第一层: FAQ** | `resume_metadata.json` 中的 7 条问答对 | 语义匹配，命中率 0.60~0.78 |
| **第二层: Metadata** | 结构化 JSON (教育/技能/项目) | 精确字段查询 + 类型过滤 |
| **第三层: 文档** | Markdown 简历，按 `##` 标题分块 | 上下文标题注入，chunk_type 标签 |

### 🔍 三级搜索回退

```
SearXNG (Bing/Baidu/Google/Wikipedia)
    ↓ 失败
DuckDuckGo (Python 库直接调用)
    ↓ 失败
DeepSeek LLM (直接回答，标注无搜索结果)
```

### 🎨 前端特性

- **DeepSeek 风格 UI** — 浅色主题，蓝色调主色
- **SSE 流式输出** — 实时打字动画，支持随时停止
- **Markdown 渲染** — 代码高亮 + 一键复制 + 表格 + 引用
- **对话管理** — 新建/切换/删除对话，侧边栏历史
- **模式切换** — Auto / Resume / Search 三种模式
- **状态感知** — 后端连接状态 + Agent 模式标签
- **PDF 下载** — 侧边栏直接下载简历

---

## 🔌 API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/health` | 健康检查 + RAG 索引统计 |
| `GET` | `/api/config` | 前端配置 (欢迎语/建议问题) |
| `POST` | `/api/chat` | **核心接口** — SSE 流式对话 |
| `POST` | `/api/rag/query` | 直接 RAG 检索 (不含 LLM) |
| `GET` | `/api/rag/stats` | RAG 向量库统计信息 |
| `POST` | `/api/rag/rebuild` | 强制重建向量索引 |
| `GET` | `/api/pdf/list` | 列出可下载的简历 PDF |
| `GET` | `/api/pdf/download/{filename}` | 下载指定 PDF 文件 |

### Chat 请求格式

```json
POST /api/chat
{
  "message": "你的问题",
  "history": [{"role": "user", "content": "..."}, ...],  // 可选
  "mode": "auto"  // "auto" | "resume" | "search"
}
```

### SSE 事件类型

| 事件 | 说明 |
|------|------|
| `metadata` | Agent 模式、搜索源、相似度 |
| `delta` | 流式文本增量 |
| `done` | 流式响应完成 |
| `error` | 错误信息 |

---

## 🚀 快速启动

### 环境要求

- **Python** 3.10+
- **Node.js** 18+
- **Docker Desktop** (运行 SearXNG)

### 1. 配置

```bash
cp .env.example .env
# 编辑 .env，填入 DeepSeek API Key
```

### 2. 启动 SearXNG

```bash
docker compose -f searxng/docker-compose.yml up -d
```

### 3. 放置知识库文件

- `markdown/` — 放入 Markdown 简历 + `resume_metadata.json`
- `pdf/` — 放入可下载的 PDF 简历

### 4. 安装 & 启动

**Windows (一键):**
```bash
start.bat
```

**手动启动:**
```bash
# 安装后端依赖
pip install -r backend/requirements.txt

# 构建前端
cd frontend && npm install && npm run build && cd ..

# 启动服务
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 5. 访问

- 本地: `http://localhost:8000`
- 公网: 如启用 Cloudflare Tunnel，启动后终端会打印 `*.trycloudflare.com` 地址

---

## ⚙️ 配置说明

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `DEEPSEEK_API_KEY` | (必填) | DeepSeek API 密钥 |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com` | API 地址 |
| `DEEPSEEK_MODEL` | `deepseek-v4-pro` | 模型名称 |
| `SEARXNG_URL` | `http://localhost:8080` | SearXNG 地址 |
| `CLOUDFLARE_AUTO_START` | `false` | 自动启动公网隧道 |
| `HOST` | `0.0.0.0` | 服务绑定地址 |
| `PORT` | `8000` | 服务端口 |

---

## 🛠️ 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| **后端框架** | FastAPI | ≥0.110 |
| **ASGI 服务器** | Uvicorn | ≥0.29 |
| **LLM** | DeepSeek API (OpenAI 兼容) | v4-pro |
| **向量数据库** | ChromaDB | ≥0.5 |
| **文本嵌入** | sentence-transformers (MiniLM-L12) | ≥2.7 |
| **PDF 解析** | PyMuPDF + RapidOCR | ≥1.24 / ≥1.3 |
| **搜索引擎** | SearXNG (Docker) + DuckDuckGo | latest |
| **前端框架** | React + TypeScript | 18.3 / 5.5 |
| **构建工具** | Vite | 5.3 |
| **CSS 框架** | Tailwind CSS | 3.4 |
| **Markdown** | react-markdown + react-syntax-highlighter | 9.0 / 15.5 |
| **图标** | Lucide React | 0.400 |
| **内网穿透** | Cloudflare Tunnel | latest |

---

## 📝 开发说明

本项目包含 `CLAUDE.md`，为 Claude Code 提供开发指引：
- 每次会话启动时阅读 `docs/` 中最新的技术文档
- 修改前端/后端代码后同步更新 `start.bat`

---

## 📄 License

MIT
