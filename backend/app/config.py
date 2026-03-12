from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://autobiz:autobiz@localhost:5432/autobiz"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str = "change-me-to-a-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    SITE_BASE_DOMAIN: str = "autobiz.app"
    GITHUB_PAT: str = ""
    VERCEL_TOKEN: str = ""
    LATE_API_KEY: str = ""
    RESEND_API_KEY: str = ""
    OPENCLAW_GATEWAY_URL: str = "http://127.0.0.1:18789"
    OPENCLAW_GATEWAY_TOKEN: str = ""

    model_config = {
        "env_file": [".env", "../.env"],
        "env_file_encoding": "utf-8",
    }


settings = Settings()
