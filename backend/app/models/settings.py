from pathlib import Path

from pydantic_settings import BaseSettings
from pydantic import Field


class InputSettings(BaseSettings):
    mongo_url: str = Field(validation_alias="MONGO_URL")
    mongo_address: str = Field(validation_alias="MONGO_ADDRESS")
    collection_name: str = Field(validation_alias="COLLECTION_NAME")
    test_collection_name: str = Field(validation_alias="TEST_COLLECTION_NAME")
    jwt_secret: str = Field(validation_alias="JWT_TOKEN")

    class Config:
        env_file = Path(__file__).resolve().parents[2] / ".env"

baseSettings = InputSettings()

class Settings:
    def __init__(self):
        self.mongo_url: str = baseSettings.mongo_url
        self.mongo_address: str = baseSettings.mongo_address
        self.collection_name: str = baseSettings.collection_name
        self.jwt_secret: str = baseSettings.jwt_secret


settings = Settings()
