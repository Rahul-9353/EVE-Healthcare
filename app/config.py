from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://eve_user:eve_pass@localhost:5432/eve_db"
    jwt_secret: str = "change-this-to-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    payment_success_rate: float = 0.8

    class Config:
        env_file = ".env"

settings = Settings()