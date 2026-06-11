import fitz  # PyMuPDF


def parse_pdf(file_path: str) -> str:
    """解析 PDF 文件为纯文本，逐页提取后拼接"""
    text_parts = []
    with fitz.open(file_path) as doc:
        for page in doc:
            text_parts.append(page.get_text())
    return "\n".join(text_parts)
