import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import engine, Base
from routers import auth, resume, analysis

# SQLite 不会自动创建父目录，必须确保 data 目录存在
os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)

# 通过 SQLAlchemy 自动建表（无迁移系统，生产环境需注意）
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI 简历诊断 SaaS",
    description="AI-powered resume analysis and optimization platform",
    version="1.0.0",
)

# CORS 白名单：开发服务器 5173、Docker nginx 3000
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://kami-l-ai-resume-diagnosis-kami.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 上传文件目录挂载为静态资源，无需鉴权即可访问
upload_dir = os.path.join(os.path.dirname(__file__), "data", "uploads")
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")

# 三大业务模块：认证、简历管理、AI 分析
app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(resume.router, prefix="/api/resumes", tags=["Resume"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])

# 健康检查端点，供 Docker / 监控探针使用
@app.get("/api/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}
