# OG Django Utils

Shared utils package for Django projects.

## Installation

```bash
pip install og-django-utils

# With encrypted media paths
pip install og-django-utils[encrypted_media_paths]
```

## Modules

### Database Backup

PostgreSQL backup tool with Django integration. Two management commands:
- `db_backup` — runs `pg_dump | gzip` locally or on EC2
- `trigger_ecs_backup` — triggers an ECS backup task

**[Full documentation →](og_django_utils/rds_backup/README.md)**

Quick start:
```bash
# Add to settings.py
INSTALLED_APPS = [..., "og_django_utils"]

# Run backup
python manage.py db_backup
```
