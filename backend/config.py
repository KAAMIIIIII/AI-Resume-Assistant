from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """全局配置，所有值均可通过 .env 文件或环境变量覆盖"""

    # 数据库 — SQLite 文件路径
    database_url: str = "sqlite:///./data/resume.db"

    # JWT — 生产环境务必修改 secret_key
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # AI — 兼容 OpenAI Chat Completions 协议，默认指向 DeepSeek
    ai_api_url: str = "https://api.openai.com/v1/chat/completions"
    ai_api_key: str = "your-api-key"
    ai_model: str = "gpt-4o-mini"

    # 文件上传目录
    upload_dir: str = "./data/uploads"

    class Config:
        env_file = ".env"
        extra = "allow"  # 允许未定义的额外环境变量，方便 Docker 注入


# 全局单例，导入即加载 .env
settings = Settings()
