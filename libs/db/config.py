from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Postgres
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="finance", env="POSTGRES_DB")
    postgres_user: str = Field(default="finance", env="POSTGRES_USER")
    postgres_password: str = Field(default="finance", env="POSTGRES_PASSWORD")

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore unknown environment variables


settings = Settings()
