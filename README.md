# AI 简历诊断

AI 驱动的简历智能分析平台。上传 PDF 简历，输入目标岗位 JD，获取六维度深度诊断报告。

## 功能特性

- 📄 **PDF 解析** — 自动提取简历文本，支持中文 PDF
- 🧠 **AI 多维度分析** — 技能、经验、学历、项目、语言、证书六维度评分
- 📊 **雷达图可视化** — ECharts 六维雷达图 + AI 自判维度权重
- ⚡ **流式 SSE 输出** — ChatGPT 风格实时流式报告生成
- 📋 **版本对比** — 历史分析记录对比，追踪简历迭代效果
- 🔐 **JWT 认证** — 用户注册/登录，数据隔离

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Vue 3 + TypeScript + Pinia + Element Plus + ECharts |
| 后端 | Python FastAPI + SQLAlchemy + SQLite |
| AI | DeepSeek / OpenAI 兼容 API |
| 部署 | Vercel + Railway |

## 快速开始

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

### 线上部署

本项目的线上部署采用了**Vercel（前端）+ Railway（后端）**的分离架构，详情见下方[部署说明](#部署说明)。

```bash
# 前端部署到 Vercel
# 1. 在 Vercel 中导入 GitHub 仓库
# 2. Root Directory 设置为 frontend
# 3. 添加环境变量 VITE_API_BASE_URL = <Railway 后端地址>

# 后端部署到 Railway
# 1. 在 Railway 中导入 GitHub 仓库
# 2. Root Directory 设置为 backend
# 3. Start Command: uvicorn main:app --host 0.0.0.0 --port 8080
# 4. 添加环境变量 AI_API_URL, AI_API_KEY, AI_MODEL, SECRET_KEY
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| AI_API_URL | AI API 端点 | `https://api.deepseek.com/chat/completions` |
| AI_API_KEY | AI API 密钥 | — |
| AI_MODEL | AI 模型名称 | `deepseek-chat` |
| SECRET_KEY | JWT 签名密钥 | — |
| DATABASE_URL | 数据库连接 | sqlite:///./data/resume.db |

## 项目结构

```
├── backend/            # FastAPI 后端
│   ├── routers/        # API 路由
│   ├── services/       # AI 分析 + PDF 解析
│   ├── models.py       # ORM 模型
│   └── schemas.py      # Pydantic 模型
├── frontend/           # Vue 3 前端
│   └── src/
│       ├── views/      # 页面组件
│       ├── components/ # 共享组件
│       ├── stores/     # Pinia 状态管理
│       └── api/        # Axios 客户端
└── docker-compose.yml
```

## License

MIT
