from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    firebase_key_file: str
    mail_username: str
    mail_password: str
    mail_from: str
    mail_port: int
    mail_server: str
    mail_from_name: str
    firebase_api_key: str

    class Config:
        env_file = ".env"

settings = Settings()
