from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://autobiz:autobiz@localhost:5432/autobiz"
    REDIS_URL: str = "redis://localhost:6379/0"
    JWT_SECRET: str = "change-me-to-a-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
