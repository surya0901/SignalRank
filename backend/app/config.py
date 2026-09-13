from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/ml-latest-small.zip"
# Independently published by TensorFlow Datasets (see docs/architecture.md).
MOVIELENS_SHA256 = "696d65a3dfceac7c45750ad32df2c259311949efec81f0f144fdfb91ebc9e436"
MOVIELENS_MIRROR = (
    "https://raw.githubusercontent.com/neaorin/databricks-workshop/master/data/ml-latest-small.zip"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "signalrank"
    postgres_user: str = "signalrank"
    postgres_password_file: Path = Path("/run/signalrank/db_password")
    data_dir: Path = Path("/data")
    dataset_url: str = MOVIELENS_URL
    dataset_sha256: str = Field(default=MOVIELENS_SHA256, pattern=r"^[a-fA-F0-9]{64}$")

    @property
    def database_url(self) -> URL:
        return URL.create(
            "postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password_file.read_text().strip(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
