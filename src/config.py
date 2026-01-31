from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    database_url: str = (
        "postgresql://roundtable:roundtable_dev_password@localhost:5432/roundtable_trading"
    )
    redis_url: str = "redis://localhost:6379/0"

    anthropic_api_key: str = ""

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    log_level: str = "INFO"
    environment: str = "development"

    kis_app_key: str = ""
    kis_app_secret: str = ""
    kis_account_number: str = ""

    backtest_start_date: str = "2020-01-01"
    backtest_initial_capital: int = 10_000_000

    max_debate_rounds: int = 5
    confidence_threshold: float = 0.7

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment == "development"


settings = Settings()
