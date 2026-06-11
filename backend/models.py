import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float,
    JSON, Enum, ForeignKey,
)
from sqlalchemy.orm import relationship

from database import Base


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"


class User(Base):
    """用户表 — 邮箱+用户名唯一，关联简历和分析记录"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.user)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # cascade: 删除用户时级联删除其所有简历和分析记录
    resumes = relationship("Resume", back_populates="owner", cascade="all, delete-orphan")
    analyses = relationship("AnalysisRecord", back_populates="owner", cascade="all, delete-orphan")


class Resume(Base):
    """简历表 — 存储 PDF 解析结果和结构化数据"""
    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    original_filename = Column(String(500), nullable=False)
    file_path = Column(String(500), nullable=False)
    # PDF 解析后的纯文本，供 AI 分析使用
    parsed_content = Column(Text, default="")
    # 预留的结构化数据字段（JSON），可用于存储 AI 提取的教育经历、技能列表等
    structured_data = Column(JSON, default=dict)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="resumes")
    analyses = relationship("AnalysisRecord", back_populates="resume", cascade="all, delete-orphan")


class AnalysisRecord(Base):
    """分析记录表 — 每次 AI 分析产生一条记录"""
    __tablename__ = "analysis_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_description = Column(Text, nullable=False)
    # 加权综合评分 (0-100)
    overall_score = Column(Float, default=0.0)
    # 6 维度分项评分: skills, experience, education, projects, language, certificates
    category_scores = Column(JSON, default=dict)
    # 详细信息 JSON: strengths, weaknesses, gap_analysis, category_weights
    details = Column(JSON, default=dict)
    # 优化建议列表，每条含 priority, category, suggestion
    suggestions = Column(JSON, default=list)
    # AI 生成的自然语言报告原文
    raw_report = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="analyses")
    resume = relationship("Resume", back_populates="analyses")
