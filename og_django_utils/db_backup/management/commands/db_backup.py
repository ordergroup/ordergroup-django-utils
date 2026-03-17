import sys

from django.core.management.base import BaseCommand

from og_django_utils.db_backup.manager import BackupManager


class Command(BaseCommand):
    help = (
        "Backup PostgreSQL databases using pg_dump | gzip. "
        "Reads DB credentials from Django settings.DATABASES. "
        "Saves to local directory or streams to S3."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--database",
            default="default",
            help="Django database alias to use (default: 'default')",
        )
        parser.add_argument(
            "--all-databases",
            action="store_true",
            default=False,
            help="Discover and back up all databases on the server (default: only Django DB)",
        )
        parser.add_argument(
            "--s3-bucket",
            default=None,
            help="S3 bucket name. If not set, saves locally (overrides settings.DB_BACKUP)",
        )
        parser.add_argument(
            "--s3-prefix",
            default=None,
            help="S3 key prefix (default: 'dumps')",
        )
        parser.add_argument(
            "--output-dir",
            default=None,
            help="Local output directory (default: './backups')",
        )
        parser.add_argument(
            "--identifier",
            default=None,
            help="Backup identifier for output path (default: database name)",
        )

    def handle(self, *args, **options):
        overrides = {}
        if options["s3_bucket"]:
            overrides["S3_BUCKET"] = options["s3_bucket"]
        if options["s3_prefix"]:
            overrides["S3_PREFIX"] = options["s3_prefix"]
        if options["output_dir"]:
            overrides["LOCAL_BACKUP_DIR"] = options["output_dir"]
        if options["identifier"]:
            overrides["IDENTIFIER"] = options["identifier"]

        try:
            manager = BackupManager(**overrides)
            exit_code = manager.backup_databases(
                database_alias=options["database"],
                all_databases=options["all_databases"],
            )
        except FileNotFoundError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            sys.exit(1)
        except ValueError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            sys.exit(1)

        if exit_code == 0:
            self.stdout.write(self.style.SUCCESS("Backup completed successfully"))
        else:
            self.stderr.write(self.style.ERROR("All backups failed"))
            sys.exit(1)
