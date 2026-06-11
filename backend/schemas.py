from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# ---------- Auth ----------

class UserRegister(BaseModel):
    """注册请求 — EmailStr 自动校验邮箱格式"""
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT 令牌响应"""
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    """用户信息输出 — 不包含密码哈希"""
    id: int
    email: str
    username: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True  # 允许从 ORM 对象直接构造


# ---------- Resume ----------

class ResumeUpdate(BaseModel):
    """简历更新 — 所有字段可选，只更新传入的非 None 字段"""
    title: Optional[str] = None
    structured_data: Optional[dict] = None
    version: Optional[int] = None


class ResumeOut(BaseModel):
    id: int
    user_id: int
    title: str
    original_filename: str
    file_path: str
    parsed_content: str
    structured_data: dict
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Analysis ----------

class AnalysisRequest(BaseModel):
    """发起 AI 分析请求"""
    resume_id: int
    job_description: str


class AnalysisOut(BaseModel):
    """分析记录输出 — resume_title 由路由层注入"""
    id: int
    user_id: int
    resume_id: int
    resume_title: str = ""
    job_description: str
    overall_score: float
    category_scores: dict
    details: dict
    suggestions: list
    raw_report: str
    created_at: datetime

    class Config:
        from_attributes = True


class CompareRequest(BaseModel):
    """版本对比请求 — 传入多个分析记录 ID"""
    analysis_ids: list[int]
