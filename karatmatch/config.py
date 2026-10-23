from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KARATMATCH_", extra="ignore")

    gold_rate_24k_inr: float = 9500.0
    host: str = "0.0.0.0"
    port: int = 8000
    data_dir: Path = Path("data")
    use_clip: bool = False

    @property
    def images_dir(self) -> Path:
        return self.data_dir / "images"

    @property
    def catalog_path(self) -> Path:
        return self.data_dir / "catalog.json"

    @property
    def index_path(self) -> Path:
        return self.data_dir / "index.npz"

    @property
    def eval_path(self) -> Path:
        return self.data_dir / "eval_report.json"


settings = Settings()
