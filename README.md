# OG Django Utils

Shared utils package for Django projects.

## Installation

```bash
pip install og-django-utils

# Database backup - direct execution (needs pg_dump + boto3)
pip install og-django-utils[db_backup]

# Database backup - ECS trigger only (needs boto3, ECS task handles backup)
pip install og-django-utils[db_backup_trigger]

# Encrypted media paths
pip install og-django-utils[encrypted_media_paths]
```

## Modules

### Database Backup

PostgreSQL backup tool with Django integration. Two management commands:
- `db_backup` — runs `pg_dump | gzip` locally or on EC2
- `trigger_db_backup` — triggers an ECS backup task

**[Full documentation →](og_django_utils/db_backup/README.md)**

Quick start:
```bash
pip install og-django-utils[db_backup]

# Add to settings.py
INSTALLED_APPS = [..., "og_django_utils"]

# Run backup
python manage.py db_backup
```
