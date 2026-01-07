import os
import logging

logger = logging.getLogger(__name__)

class Config:
    BOT_TOKEN: str
    DATABASE_URL: str
    ADMIN_BOOTSTRAP_CODES: list[str]
    ARCHIVE_AFTER_DAYS: int
    LOG_LEVEL: str
    ENVIRONMENT: str
    RESPONSE_REMINDER_HOURS: int
    JOB_AUTO_CLOSE_HOURS: int

    def __init__(self):
        self.BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.DATABASE_URL = os.getenv("DATABASE_URL", "")
        
        admin_codes = os.getenv("ADMIN_BOOTSTRAP_CODES", "")
        self.ADMIN_BOOTSTRAP_CODES = [c.strip() for c in admin_codes.split(",") if c.strip()]
        
        self.ARCHIVE_AFTER_DAYS = int(os.getenv("ARCHIVE_AFTER_DAYS", "90"))
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
        self.RESPONSE_REMINDER_HOURS = int(os.getenv("RESPONSE_REMINDER_HOURS", "24"))
        self.JOB_AUTO_CLOSE_HOURS = int(os.getenv("JOB_AUTO_CLOSE_HOURS", "72"))

    def validate(self) -> bool:
        errors = []
        
        if not self.BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN is required")
        
        if not self.DATABASE_URL:
            errors.append("DATABASE_URL is required")
        
        if not self.ADMIN_BOOTSTRAP_CODES:
            errors.append("ADMIN_BOOTSTRAP_CODES is required (comma-separated admin codes)")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            return False
        
        return True

    def setup_logging(self):
        level = getattr(logging, self.LOG_LEVEL.upper(), logging.INFO)
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

config = Config()
