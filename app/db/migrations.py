from alembic import command
from alembic.config import Config
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class DatabaseMigration:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.alembic_cfg = Config()
        self.alembic_cfg.set_main_option(
            "script_location",
            str(Path(__file__).parent / "migrations")
        )
        self.alembic_cfg.set_main_option(
            "sqlalchemy.url",
            database_url
        )

    async def upgrade(self, revision: str = "head") -> None:
        try:
            command.upgrade(self.alembic_cfg, revision)
            logger.info(f"Database upgraded to revision {revision}")
        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            raise

    async def downgrade(self, revision: str) -> None:
        try:
            command.downgrade(self.alembic_cfg, revision)
            logger.info(f"Database downgraded to revision {revision}")
        except Exception as e:
            logger.error(f"Downgrade failed: {str(e)}")
            raise
