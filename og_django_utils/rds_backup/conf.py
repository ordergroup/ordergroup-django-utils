import os

from django.conf import settings

from .constants import (
    DEFAULT_AWS_REGION,
    DEFAULT_EXCLUDE,
    DEFAULT_LOCAL_BACKUP_DIR,
    DEFAULT_S3_PREFIX,
    DEFAULT_S3_STORAGE_CLASS,
    DEFAULT_TIMESTAMP_FORMAT,
)


def get_config() -> dict:
    """Merge settings.RDS_BACKUP with defaults and env var fallbacks.

    Priority: settings.RDS_BACKUP > environment variable > default value.
    """
    user_conf = getattr(settings, "RDS_BACKUP", {})

    return {
        "S3_BUCKET": user_conf.get(
            "S3_BUCKET",
            os.environ.get("BACKUP_S3_BUCKET", ""),
        ),
        "S3_PREFIX": user_conf.get(
            "S3_PREFIX",
            os.environ.get("BACKUP_S3_PREFIX", DEFAULT_S3_PREFIX),
        ),
        "S3_STORAGE_CLASS": user_conf.get(
            "S3_STORAGE_CLASS",
            os.environ.get("BACKUP_S3_STORAGE_CLASS", DEFAULT_S3_STORAGE_CLASS),
        ),
        "LOCAL_BACKUP_DIR": user_conf.get(
            "LOCAL_BACKUP_DIR",
            os.environ.get("BACKUP_LOCAL_DIR", DEFAULT_LOCAL_BACKUP_DIR),
        ),
        "DB_EXCLUDE": set(user_conf.get("DB_EXCLUDE", DEFAULT_EXCLUDE)),
        "IDENTIFIER": user_conf.get(
            "IDENTIFIER",
            os.environ.get("BACKUP_IDENTIFIER", ""),
        ),
        "AWS_REGION": user_conf.get(
            "AWS_REGION",
            os.environ.get("AWS_REGION"),
        ),
        "TIMESTAMP_FORMAT": user_conf.get(
            "TIMESTAMP_FORMAT",
            DEFAULT_TIMESTAMP_FORMAT,
        ),
        "ECS_CLUSTER": user_conf.get(
            "ECS_CLUSTER",
            os.environ.get("BACKUP_ECS_CLUSTER", ""),
        ),
        "ECS_TASK_DEFINITION": user_conf.get(
            "ECS_TASK_DEFINITION",
            os.environ.get("BACKUP_ECS_TASK_DEFINITION", "db-ops-backup"),
        ),
    }


def get_db_credentials(database_alias: str = "default") -> dict:
    """Extract connection parameters from Django settings.DATABASES."""
    db_settings = settings.DATABASES.get(database_alias)
    if not db_settings:
        raise ValueError(f"Database alias '{database_alias}' not found in settings.DATABASES")

    engine = db_settings.get("ENGINE", "")
    if "postgresql" not in engine and "postgis" not in engine:
        raise ValueError(f"Database '{database_alias}' uses engine '{engine}', but only PostgreSQL is supported")

    return {
        "host": db_settings.get("HOST") or "localhost",
        "port": int(db_settings.get("PORT") or 5432),
        "user": db_settings.get("USER", ""),
        "password": db_settings.get("PASSWORD", ""),
        "name": db_settings.get("NAME", ""),
    }
