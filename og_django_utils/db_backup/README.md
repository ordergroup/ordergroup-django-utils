# Database Backup Module

PostgreSQL backup tool integrated with Django. Reads credentials from `settings.DATABASES` — no manual env var configuration needed.

## Installation

```bash
# For direct backups with S3 upload (needs pg_dump on host)
pip install og-django-utils[db_backup]

# For ECS trigger only (ECS task handles S3 upload)
pip install og-django-utils[db_backup_trigger]
```

**Both options support S3 backups:**
- `db_backup` — your Django app uploads to S3 (needs boto3 + pg_dump locally)
- `trigger_db_backup` — ECS task uploads to S3 (only needs boto3 to trigger the task)

## Two commands

| Command | What it does | Needs `pg_dump`? | Needs `boto3`? |
|---|---|---|---|
| `db_backup` | Runs `pg_dump \| gzip`, saves locally or to S3 | Yes | Only for S3 |
| `trigger_db_backup` | Triggers an ECS backup task on AWS | No | Yes |

## Setup

1. Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "og_django_utils.db_backup",
]
```

2. Optionally configure in `settings.py`:

```python
DB_BACKUP = {
    # S3 upload (leave empty for local mode)
    "S3_BUCKET": "",
    "S3_PREFIX": "dumps",
    "S3_STORAGE_CLASS": "STANDARD_IA",

    # Local backup directory
    "LOCAL_BACKUP_DIR": "./backups",

    # Backup identifier (default: database name)
    "IDENTIFIER": "myapp",

    # Databases to exclude from --all-databases
    "DB_EXCLUDE": ["postgres", "template0", "template1", "rdsadmin"],

    # AWS
    "AWS_REGION": "eu-central-1",

    # ECS trigger settings
    "ECS_CLUSTER": "my-cluster",
    "ECS_TASK_DEFINITION": "db-ops-backup",
}
```

All settings have sensible defaults. For local development, you may not need any configuration at all.

## Usage: `db_backup`

Runs backup directly. Requires `pg_dump` binary on the host.

```bash
# Back up Django's database locally
python manage.py db_backup

# Back up to S3
python manage.py db_backup --s3-bucket my-backups

# Back up all databases on the server
python manage.py db_backup --all-databases

# Custom output directory
python manage.py db_backup --output-dir /tmp/dumps

# Use a different Django database alias
python manage.py db_backup --database replica
```

### When to use

- **Local development** — test backups against your dev database
- **EC2 deployments** — run backups directly on the server
- **Bastion tunnels** — backup remote databases through SSH tunnel
- **Any environment with `pg_dump` installed**

## Usage: `trigger_db_backup`

Triggers an ECS task to run the backup. No `pg_dump` needed — the ECS task container handles it.

```bash
# Trigger using settings.DB_BACKUP config
python manage.py trigger_db_backup

# Override cluster/task
python manage.py trigger_db_backup --cluster prod --task-definition db-ops-backup
```

### Programmatic usage

```python
from django.core.management import call_command

# From a Celery task
@app.task
def nightly_backup():
    call_command("trigger_db_backup")

# From a Django admin action
@admin.action(description="Trigger database backup")
def trigger_backup(modeladmin, request, queryset):
    call_command("trigger_db_backup")

# From an API endpoint
@api_view(['POST'])
@permission_classes([IsAdminUser])
def trigger_backup(request):
    call_command("trigger_db_backup")
    return Response({"status": "Backup task started"})
```

### When to use

- **ECS/Fargate containers** — your Django app doesn't have `pg_dump`
- **On-demand backups** — trigger from admin, API, or Celery
- **Scheduled backups** — via Celery Beat or Django-Q

**Note:** This requires the db-ops Docker image to be deployed on ECS. See [db-ops deployment docs](https://github.com/ordergroup/og-db-backup-utils).

## Configuration priority

Settings are resolved in this order:

1. Command-line arguments (e.g., `--s3-bucket`)
2. `settings.DB_BACKUP` dict
3. Environment variables (prefixed with `BACKUP_`)
4. Default values

| Setting | Env var fallback | Default |
|---|---|---|
| `S3_BUCKET` | `BACKUP_S3_BUCKET` | empty (local mode) |
| `S3_PREFIX` | `BACKUP_S3_PREFIX` | `dumps` |
| `S3_STORAGE_CLASS` | `BACKUP_S3_STORAGE_CLASS` | `STANDARD_IA` |
| `LOCAL_BACKUP_DIR` | `BACKUP_LOCAL_DIR` | `./backups` |
| `IDENTIFIER` | `BACKUP_IDENTIFIER` | database name |
| `AWS_REGION` | `AWS_REGION` | `eu-central-1` |
| `ECS_CLUSTER` | `BACKUP_ECS_CLUSTER` | empty |
| `ECS_TASK_DEFINITION` | `BACKUP_ECS_TASK_DEFINITION` | `db-ops-backup` |

## Examples

### Local development backup

```bash
# Minimal - backs up Django's database to ./backups/
python manage.py db_backup
```

### Production EC2 with S3

```python
# settings.py
DB_BACKUP = {
    "S3_BUCKET": "mycompany-db-backups",
    "IDENTIFIER": "myapp-prod",
}
```

```bash
# Run on EC2
python manage.py db_backup
```

### ECS containers with Celery scheduling

```python
# settings.py
DB_BACKUP = {
    "ECS_CLUSTER": "production",
    "ECS_TASK_DEFINITION": "db-ops-backup",
}

# tasks.py
from celery import app
from django.core.management import call_command

@app.task
def nightly_backup():
    call_command("trigger_db_backup")

# celerybeat schedule
CELERY_BEAT_SCHEDULE = {
    'nightly-backup': {
        'task': 'myapp.tasks.nightly_backup',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

### Backup all databases on server

```bash
# Discovers all databases on PostgreSQL server and backs them up
python manage.py db_backup --all-databases --s3-bucket my-backups
```

## Requirements

### For `db_backup` command

- `pg_dump` binary installed on the host
  - Ubuntu/Debian: `apt install postgresql-client`
  - macOS: `brew install postgresql`
  - Alpine: `apk add postgresql-client`
- `boto3` (if using S3): `pip install og-django-utils[db_backup]`

### For `trigger_db_backup` command

- `boto3`: `pip install og-django-utils[db_backup_trigger]`
- AWS credentials configured (IAM role or environment variables)
- ECS task definition deployed (see db-ops repo)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Django App (ECS Container)                                  │
│                                                              │
│  python manage.py trigger_db_backup                         │
│         ↓                                                    │
│  boto3.ecs.run_task()                                       │
└──────────────────────┬──────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────────────────┐
│ ECS Task (db-ops Docker image)                              │
│                                                              │
│  pg_dump | gzip → S3                                        │
│                                                              │
│  Has: pg_dump binary, boto3, psycopg                        │
└─────────────────────────────────────────────────────────────┘
```

The `trigger_db_backup` command is a thin wrapper that calls AWS ECS API. The actual backup runs in a separate container that has all the required tools.
