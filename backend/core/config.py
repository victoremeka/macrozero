from pydantic import BaseSettings, Field


class DatabaseSettings(BaseSettings):
    host: str = Field(..., env="DB_HOST")
    port: int | None = Field(None, env="DB_PORT")
    username: str = Field(..., env="DB_USERNAME")
    password: str = Field(..., env="DB_PASSWORD")
    database: str = Field(..., env="DB_DATABASE")


class GithubSettings(BaseSettings):
    app_id: str | None = Field(None, env="APP_ID")
    installation_id: str | None = Field(None, env="INSTALLATION_ID")
    webhook_secret: str | None = Field(None, env="WEBHOOK_SECRET")
    private_key_path: str | None = Field(None, env="PRIVATE_KEY_PATH")
    token: str | None = Field(None, env="GITHUB_TOKEN")


class Settings(BaseSettings):
    db: DatabaseSettings = DatabaseSettings()
    github: GithubSettings = GithubSettings()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
