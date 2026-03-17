DEFAULT_EXCLUDE = frozenset({
    "postgres",
    "template0",
    "template1",
    "rdsadmin",
})

DEFAULT_TIMESTAMP_FORMAT = "%Y%m%d_%H%M%S"

DEFAULT_S3_PREFIX = "dumps"
DEFAULT_S3_STORAGE_CLASS = "STANDARD_IA"
DEFAULT_LOCAL_BACKUP_DIR = "./backups"
DEFAULT_AWS_REGION = "eu-central-1"
