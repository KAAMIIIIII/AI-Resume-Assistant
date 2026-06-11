import json
from typing import AsyncGenerator

import httpx

from config import settings

# 核心系统提示词：定义 AI 的角色和输出格式规范
# 输出分两部分：自然语言报告 + <!--JSON--> 分隔符 + JSON 结构化数据
SYSTEM_PROMPT = """你是一位资深 HR 和简历优化专家。请根据以下简历内容和岗位 JD，进行深度分析。

**输出格式要求：**

第一部分：先写一份自然语言的分析报告（300-500字），包括：
- 整体匹配度评价
- 各维度的详细分析（技能、经验、学历、项目、语言、证书）
- 核心优势和不足之处
- 具体可操作的优化建议

第二部分：在报告末尾另起一行，写上分隔标记 `<!--JSON-->`，然后紧跟一个 JSON 对象。

JSON 结构说明：
{
  "category_scores": {
    "skills": 0-100 的技能匹配度,
    "experience": 0-100 的经验匹配度,
    "education": 0-100 的学历匹配度,
    "projects": 0-100 的项目经验匹配度,
    "language": 0-100 的语言能力,
    "certificates": 0-100 的证书资质
  },
  "category_weights": {
    "skills": 该岗位对技能的要求权重(0-1),
    "experience": 该岗位对经验的要求权重(0-1),
    "education": 该岗位对学历的要求权重(0-1),
    "projects": 该岗位对项目经验的要求权重(0-1),
    "language": 该岗位对语言的要求权重(0-1),
    "certificates": 该岗位对证书的要求权重(0-1)
  },
  "details": {
    "strengths": ["优势1", "优势2"],
    "weaknesses": ["不足1", "不足2"],
    "gap_analysis": "差距分析描述"
  },
  "suggestions": [
    {"priority": "high/medium/low", "category": "分类", "suggestion": "具体优化建议"}
  ]
}

**重要规则：**
1. 第一部分报告用流畅自然的中文，像一位资深 HR 在面对面给出建议
2. category_weights 各维度权重之和应接近 1.0，根据 JD 侧重点分配
3. JSON 部分必须合法可解析，不要用 markdown 代码块包裹
4. 不要生成 overall_score 字段，系统会自动加权计算
5. 分隔标记 `<!--JSON-->` 必须独占一行，紧贴在 JSON 之前
"""


def _calc_overall(category_scores: dict, weights: dict = None) -> float:
    """根据 6 个维度分数 × AI 权重做加权平均，得出综合评分 (0-100)。
    无权重时退化为简单算术平均。
    """
    if not weights:
        scores = [v for v in category_scores.values() if isinstance(v, (int, float))]
        return round(sum(scores) / len(scores), 1) if scores else 0.0

    weighted_sum = 0.0
    total_weight = 0.0
    for key, score in category_scores.items():
        w = weights.get(key, 0)
        if isinstance(score, (int, float)) and isinstance(w, (int, float)):
            weighted_sum += score * w
            total_weight += w

    if total_weight == 0:
        return 0.0
    return round(weighted_sum / total_weight, 1)


def _build_prompt(resume_text: str, job_description: str) -> str:
    """组装用户消息：简历全文 + 岗位描述"""
    return f"""## 简历内容
{resume_text}

## 岗位 JD
{job_description}

请根据上述简历和 JD 进行分析，返回 JSON 格式的分析报告。"""


def analyze_resume_sync(resume_text: str, job_description: str) -> dict:
    """同步 AI 分析：发送简历+JD 到 AI API，解析返回的报告和 JSON。
    返回包含 raw_report、overall_score、category_scores、details、suggestions 的字典。
    超时时间 60s。
    """
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(
            settings.ai_api_url,
            headers={
                "Authorization": f"Bearer {settings.ai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.ai_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _build_prompt(resume_text, job_description)},
                ],
                "temperature": 0.3,  # 低温度保证输出稳定
                "max_tokens": 4096,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]

    # 以 <!--JSON--> 为界分割自然语言报告和结构化数据
    if "<!--JSON-->" in content:
        raw_report, json_part = content.split("<!--JSON-->", 1)
        raw_report = raw_report.strip()
        json_part = json_part.strip()
    else:
        # 兼容旧格式（纯 JSON 无报告）
        raw_report = ""
        json_part = content

    # 解析 JSON，容错处理
    try:
        result = json.loads(json_part)
    except json.JSONDecodeError:
        result = {
            "overall_score": 0,
            "category_scores": {},
            "details": {},
            "suggestions": [],
        }
    result["raw_report"] = raw_report

    # 综合分 = 6 个维度 × AI 权重，加权平均（前端直接展示）
    cats = result.get("category_scores", {})
    weights = result.get("category_weights", {})
    if cats:
        result["overall_score"] = _calc_overall(cats, weights)

    # 权重合并进 details，前端可读取展示各维度重要性
    details = result.setdefault("details", {})
    details["category_weights"] = weights
    return result


async def analyze_resume_stream(
    resume_text: str, job_description: str
) -> AsyncGenerator[str, None]:
    """流式 AI 分析：通过 SSE 逐步产出 AI 生成的文本片段。
    路由层负责收集全部片段后再做 JSON 解析和入库。
    超时时间 120s（流式响应通常更慢）。
    """
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            settings.ai_api_url,
            headers={
                "Authorization": f"Bearer {settings.ai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.ai_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": _build_prompt(resume_text, job_description)},
                ],
                "temperature": 0.3,
                "max_tokens": 4096,
                "stream": True,  # 启用流式输出
            },
        ) as response:
            response.raise_for_status()
            # 逐行读取 SSE 事件流
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]  # 去掉 "data: " 前缀
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue  # 忽略无法解析的行
