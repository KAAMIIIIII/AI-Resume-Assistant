import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from database import get_db
from models import User, Resume
from schemas import ResumeUpdate, ResumeOut
from auth import get_current_user
from config import settings
from services.pdf_parser import parse_pdf

router = APIRouter()


@router.get("/", response_model=list[ResumeOut])
def list_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取当前用户的简历列表，按更新时间倒序"""
    return (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.updated_at.desc())
        .all()
    )


@router.post("/upload", response_model=ResumeOut)
async def upload_resume(
    title: str = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传 PDF 简历 — 保存文件、解析文本、创建数据库记录"""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="仅支持 PDF 文件")

    upload_dir = settings.upload_dir
    os.makedirs(upload_dir, exist_ok=True)

    # UUID 前缀避免文件名冲突
    filename = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # 上传后立即解析 PDF 文本，供后续 AI 分析使用
    parsed_text = parse_pdf(file_path)

    resume = Resume(
        user_id=current_user.id,
        title=title,
        original_filename=file.filename,
        file_path=file_path,
        parsed_content=parsed_text,
        structured_data={},
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    return resume


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单份简历详情 — 校验归属权限"""
    resume = db.query(Resume).filter(
        Resume.id == resume_id, Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")
    return resume


@router.put("/{resume_id}", response_model=ResumeOut)
def update_resume(
    resume_id: int,
    payload: ResumeUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """更新简历信息 — 只更新传入的非 None 字段"""
    resume = db.query(Resume).filter(
        Resume.id == resume_id, Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    if payload.title is not None:
        resume.title = payload.title
    if payload.structured_data is not None:
        resume.structured_data = payload.structured_data
    if payload.version is not None:
        resume.version = payload.version

    db.commit()
    db.refresh(resume)
    return resume


@router.delete("/{resume_id}")
def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除简历 — 同时删除服务器上的 PDF 文件"""
    resume = db.query(Resume).filter(
        Resume.id == resume_id, Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    # 清理物理文件
    if os.path.exists(resume.file_path):
        os.remove(resume.file_path)

    db.delete(resume)
    db.commit()
    return {"message": "简历已删除"}
