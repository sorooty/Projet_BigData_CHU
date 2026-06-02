from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    """Paramètres globaux du projet, chargés depuis .env."""

    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int
    pseudonymization_key: str

    @property
    def sqlalchemy_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


def load_settings() -> Settings:
    # Point d'entrée unique pour la config.
    # Si une variable manque, on veut planter tôt.
    load_dotenv()
    return Settings(
        postgres_db=os.environ["POSTGRES_DB"],
        postgres_user=os.environ["POSTGRES_USER"],
        postgres_password=os.environ["POSTGRES_PASSWORD"],
        postgres_host=os.environ.get("POSTGRES_HOST", "localhost"),
        postgres_port=int(os.environ.get("POSTGRES_PORT", "5432")),
        pseudonymization_key=os.environ["PSEUDONYMIZATION_KEY"],
    )
