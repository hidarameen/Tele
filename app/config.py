from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
	app_env: str = Field(default="development", alias="APP_ENV")
	app_locale: str = Field(default="ar", alias="APP_LOCALE")
	app_tz: str = Field(default="Asia/Riyadh", alias="APP_TZ")
	app_encryption_key: str = Field(default="", alias="APP_ENCRYPTION_KEY")

	builder_bot_token: str = Field(default="", alias="BUILDER_BOT_TOKEN")

	database_url: str | None = Field(default=None, alias="DATABASE_URL")
	redis_url: str = Field(..., alias="REDIS_URL")

	# Optional param-based DB config
	db_host: str | None = Field(default=None, alias="DB_HOST")
	db_port: int | None = Field(default=None, alias="DB_PORT")
	db_name: str | None = Field(default=None, alias="DB_NAME")
	db_user: str | None = Field(default=None, alias="DB_USER")
	db_password: str | None = Field(default=None, alias="DB_PASSWORD")
	db_sslmode: str | None = Field(default=None, alias="DB_SSLMODE")  # disable/allow/prefer/require/verify-ca/verify-full

	telethon_api_id: int | None = Field(default=None, alias="TELETHON_API_ID")
	telethon_api_hash: str | None = Field(default=None, alias="TELETHON_API_HASH")

	class Config:
		env_file = ".env"
		env_file_encoding = "utf-8"

settings = Settings()