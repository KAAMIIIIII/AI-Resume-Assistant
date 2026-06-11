import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from models import User, Resume, AnalysisRecord
from schemas import AnalysisRequest, AnalysisOut, CompareRequest
from auth import get_current_user
from services.ai_analyzer import analyze_resume_stream, _calc_overall

router = APIRouter()


@router.post("/", response_model=AnalysisOut)
def create_analysis(
    payload: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """同步 AI 分析 — 等待完整结果后返回，适合简单集成场景"""
    resume = db.query(Resume).filter(
        Resume.id == payload.resume_id, Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    # 延迟导入避免循环依赖
    from services.ai_analyzer import analyze_resume_sync

    result = analyze_resume_sync(resume.parsed_content, payload.job_description)

    # 分析结果持久化
    record = AnalysisRecord(
        user_id=current_user.id,
        resume_id=resume.id,
        job_description=payload.job_description,
        overall_score=result["overall_score"],
        category_scores=result["category_scores"],
        details=result["details"],
        suggestions=result["suggestions"],
        raw_report=result["raw_report"],
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.post("/stream")
async def create_analysis_stream(
    payload: AnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """流式 AI 分析（SSE）— 前端实时展示 AI 生成过程，体验更好。
    数据流：流式 chunk → 前端累积显示 → 完成后解析 JSON → 入库并通知前端。
    """
    resume = db.query(Resume).filter(
        Resume.id == payload.resume_id, Resume.user_id == current_user.id
    ).first()
    if not resume:
        raise HTTPException(status_code=404, detail="简历不存在")

    async def event_generator():
        try:
            # 阶段 1：收集 AI 流式输出
            full_text = ""
            async for chunk in analyze_resume_stream(resume.parsed_content, payload.job_description):
                full_text += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

            # 阶段 2：以 <!--JSON--> 为界分割自然语言报告和结构化数据
            if "<!--JSON-->" in full_text:
                raw_report, json_part = full_text.split("<!--JSON-->", 1)
                raw_report = raw_report.strip()
                json_part = json_part.strip()
            else:
                raw_report = full_text
                json_part = full_text

            # 阶段 3：解析 JSON（容错处理）
            try:
                parsed = json.loads(json_part)
            except json.JSONDecodeError:
                parsed = {
                    "overall_score": 0,
                    "category_scores": {},
                    "details": {},
                    "suggestions": [],
                }

            # 阶段 4：计算加权综合分并入库
            cats = parsed.get("category_scores", {})
            weights = parsed.get("category_weights", {})
            if cats:
                parsed["overall_score"] = _calc_overall(cats, weights)

            details = parsed.get("details", {})
            details["category_weights"] = weights

            record = AnalysisRecord(
                user_id=current_user.id,
                resume_id=resume.id,
                job_description=payload.job_description,
                overall_score=parsed.get("overall_score", 0),
                category_scores=parsed.get("category_scores", {}),
                details=details,
                suggestions=parsed.get("suggestions", []),
                raw_report=raw_report,
            )
            db.add(record)
            db.commit()
            db.refresh(record)

            # 通知前端分析完成，附带 analysis_id 用于跳转
            yield f"data: {json.dumps({'done': True, 'analysis_id': record.id})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get("/", response_model=list[AnalysisOut])
def list_analyses(
    resume_id: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取分析记录列表 — 可选按简历 ID 过滤"""
    query = db.query(AnalysisRecord).filter(
        AnalysisRecord.user_id == current_user.id
    )
    if resume_id:
        query = query.filter(AnalysisRecord.resume_id == resume_id)

    records = query.order_by(AnalysisRecord.created_at.desc()).all()

    # 批量查询关联简历标题，避免 N+1 查询
    resume_ids = {r.resume_id for r in records}
    resumes = {
        r.id: r.title
        for r in db.query(Resume).filter(Resume.id.in_(resume_ids)).all()
    }
    for record in records:
        record.resume_title = resumes.get(record.resume_id, "")

    return records


@router.get("/{analysis_id}", response_model=AnalysisOut)
def get_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取单条分析记录详情 — 附带简历标题"""
    record = db.query(AnalysisRecord).filter(
        AnalysisRecord.id == analysis_id,
        AnalysisRecord.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="分析记录不存在")

    resume = db.query(Resume).filter(Resume.id == record.resume_id).first()
    record.resume_title = resume.title if resume else ""

    return record


@router.delete("/{analysis_id}")
def delete_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """删除分析记录"""
    record = db.query(AnalysisRecord).filter(
        AnalysisRecord.id == analysis_id,
        AnalysisRecord.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="分析记录不存在")
    db.delete(record)
    db.commit()
    return {"message": "分析记录已删除"}


@router.post("/compare")
def compare_analyses(
    payload: CompareRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """版本对比 — 传入多个分析 ID，返回各版本的评分和维度分数，前端用图表可视化"""
    records = (
        db.query(AnalysisRecord)
        .filter(
            AnalysisRecord.id.in_(payload.analysis_ids),
            AnalysisRecord.user_id == current_user.id,  # 确保只能对比自己的分析
        )
        .all()
    )
    if len(records) != len(payload.analysis_ids):
        raise HTTPException(status_code=404, detail="部分分析记录不存在")

    return {
        "analyses": [
            {
                "id": r.id,
                "resume_id": r.resume_id,
                "created_at": r.created_at.isoformat(),
                "overall_score": r.overall_score,
                "category_scores": r.category_scores,
            }
            for r in records
        ]
    }
