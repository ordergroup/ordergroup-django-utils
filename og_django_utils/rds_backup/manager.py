import logging
import os
import shutil
import subprocess
import time
from pathlib import Path

from django.db import connections

from og_django_utils.rds_backup.conf import get_config, get_db_credentials

logger = logging.getLogger("og.rds_backup")


class RDSBackupManager:
    """RDS PostgreSQL backup manager integrated with Django.

    Reads database credentials from ``settings.DATABASES`` and backup
    configuration from ``settings.RDS_BACKUP``.  Runs a ``pg_dump | gzip``
    pipeline and streams the output to **S3** or saves it **locally**.

    Two Django management commands expose this class:

    ``db_backup`` — direct backup (requires ``pg_dump`` on the host)::

        # back up the default Django database to a local directory
        python manage.py db_backup

        # back up to S3
        python manage.py db_backup --s3-bucket my-backups

        # back up every database on the PostgreSQL server
        python manage.py db_backup --all-databases

    ``trigger_ecs_backup`` — trigger an ECS task that runs the backup::

        # trigger using settings.RDS_BACKUP config
        python manage.py trigger_ecs_backup

        # override cluster and task definition
        python manage.py trigger_ecs_backup --cluster prod --task-definition db-ops-backup

    Programmatic usage::

        from og_django_utils.rds_backup.manager import RDSBackupManager

        manager = RDSBackupManager(S3_BUCKET="my-bucket")
        exit_code = manager.backup_databases()          # single DB
        exit_code = manager.backup_databases(all_databases=True)  # all DBs

    Environment variables / settings.RDS_BACKUP required for S3 mode:

    - ``S3_BUCKET``  — target S3 bucket name
    - ``AWS_REGION``  — AWS region (default ``eu-central-1``)

    For ECS trigger mode (``trigger_ecs_backup`` command):

    - ``ECS_CLUSTER``  — ECS cluster name (required)
    - ``ECS_TASK_DEFINITION`` — task definition (default ``db-ops-backup``)
    """

    def __init__(self, **overrides):
        config = get_config()
        config.update({k: v for k, v in overrides.items() if v is not None})

        self.s3_bucket = config["S3_BUCKET"]
        self.s3_prefix = config["S3_PREFIX"].strip("/")
        self.s3_storage_class = config["S3_STORAGE_CLASS"]
        self.local_backup_dir = config["LOCAL_BACKUP_DIR"]
        self.db_exclude = config["DB_EXCLUDE"]
        self.identifier = config["IDENTIFIER"]
        self.region = config["AWS_REGION"]
        self.timestamp = time.strftime(config["TIMESTAMP_FORMAT"])

        self.use_s3 = bool(self.s3_bucket)
        self._s3_client = None

        self.results: dict[str, bool] = {}

    def backup_databases(
        self,
        database_alias: str = "default",
        all_databases: bool = False,
    ) -> int:
        """Back up one or more PostgreSQL databases.

        Reads credentials from ``settings.DATABASES[database_alias]``.
        When *all_databases* is ``True``, discovers every non-template
        database on the server and backs them all up.

        Returns ``0`` on success, ``1`` if every backup failed.
        """
        self._check_pg_dump()

        creds = get_db_credentials(database_alias)
        host = creds["host"]
        port = creds["port"]
        user = creds["user"]
        password = creds["password"]
        identifier = self.identifier or creds["name"]

        start = time.monotonic()

        if not self.use_s3:
            logger.info("S3 not configured — saving dumps locally to %s", self.local_backup_dir)

        if all_databases:
            databases = self.get_databases(database_alias)
            if not databases:
                logger.warning("No databases to back up")
                return 1
            logger.info("Databases: %s", ", ".join(databases))
        else:
            db_name = creds["name"]
            if not db_name:
                raise ValueError("No database name in Django settings.DATABASES")
            databases = [db_name]
            logger.info("Backing up database: %s", db_name)

        for db_name in databases:
            key = f"{identifier}/{db_name}"
            if self.use_s3:
                self.results[key] = self._dump_to_s3(host, port, user, password, db_name, identifier)
            else:
                self.results[key] = self._dump_to_local_storage(host, port, user, password, db_name, identifier)

        elapsed = time.monotonic() - start
        total = len(self.results)
        succeeded = sum(1 for v in self.results.values() if v)
        failed = total - succeeded

        logger.info(
            "Done in %.1fs — %d/%d succeeded, %d failed",
            elapsed,
            succeeded,
            total,
            failed,
        )

        if failed:
            logger.warning(
                "Failed: %s",
                ", ".join(k for k, v in self.results.items() if not v),
            )

        if total > 0 and failed == total:
            return 1
        return 0

    def get_databases(self, database_alias: str = "default") -> list[str]:
        """List non-template, connectable databases on the PostgreSQL server.

        Uses Django's database connection for the given *database_alias*
        and excludes system databases (``postgres``, ``template0``, etc.).
        """
        connection = connections[database_alias]
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT datname FROM pg_database WHERE datistemplate = false AND datallowconn = true ORDER BY datname"
            )
            all_dbs = [row[0] for row in cursor.fetchall()]
        return [db for db in all_dbs if db not in self.db_exclude]

    @property
    def s3_client(self):
        if self._s3_client is None:
            try:
                import boto3
            except ImportError as exc:
                raise ImportError("boto3 is required for S3 uploads but not found. Reinstall og-django-utils.") from exc
            self._s3_client = boto3.client("s3", region_name=self.region)
        return self._s3_client

    def _check_pg_dump(self) -> None:
        if not shutil.which("pg_dump"):
            raise FileNotFoundError(
                "pg_dump not found. Install postgresql-client: apt install postgresql-client / brew install postgresql"
            )

    def _start_pipeline(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        db_name: str,
        identifier: str,
    ) -> tuple[subprocess.Popen, subprocess.Popen] | None:
        env = {**os.environ, "PGPASSWORD": password}
        pg_dump_cmd = [
            "pg_dump",
            "--no-owner",
            "--clean",
            "--if-exists",
            "-h",
            host,
            "-p",
            str(port),
            "-U",
            user,
            "-d",
            db_name,
        ]

        try:
            p_dump = subprocess.Popen(
                pg_dump_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
            )
            p_gzip = subprocess.Popen(
                ["gzip", "-9"],
                stdin=p_dump.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            p_dump.stdout.close()
        except Exception as exc:
            logger.error("[%s/%s] Failed to start pipeline: %s", identifier, db_name, exc)
            return None

        return p_dump, p_gzip

    def _wait_and_check(
        self,
        p_dump: subprocess.Popen,
        p_gzip: subprocess.Popen,
        identifier: str,
        db_name: str,
    ) -> bool:
        p_gzip.wait()
        p_dump.wait()

        errors = self._collect_errors([("pg_dump", p_dump), ("gzip", p_gzip)])
        if errors:
            for step, rc, msg in errors:
                logger.error(
                    "[%s/%s] %s failed (rc=%d): %s",
                    identifier,
                    db_name,
                    step,
                    rc,
                    msg,
                )
            return False
        return True

    @staticmethod
    def _collect_errors(
        procs: list[tuple[str, subprocess.Popen]],
    ) -> list[tuple[str, int, str]]:
        errors: list[tuple[str, int, str]] = []
        for name, proc in procs:
            if proc.returncode != 0:
                stderr = ""
                if proc.stderr:
                    stderr = proc.stderr.read().decode(errors="replace").strip()
                errors.append((name, proc.returncode, stderr))
            if proc.stderr:
                proc.stderr.close()
        return errors

    def _dump_to_s3(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        db_name: str,
        identifier: str,
    ) -> bool:
        s3_key = f"{self.s3_prefix}/{identifier}/{db_name}-{self.timestamp}.sql.gz"
        logger.info(
            "[%s/%s] Dumping -> s3://%s/%s",
            identifier,
            db_name,
            self.s3_bucket,
            s3_key,
        )

        pipeline = self._start_pipeline(host, port, user, password, db_name, identifier)
        if not pipeline:
            return False
        p_dump, p_gzip = pipeline

        try:
            self.s3_client.upload_fileobj(
                Fileobj=p_gzip.stdout,
                Bucket=self.s3_bucket,
                Key=s3_key,
                ExtraArgs={"StorageClass": self.s3_storage_class},
            )
        except Exception as exc:
            logger.error("[%s/%s] S3 upload failed: %s", identifier, db_name, exc)
            p_gzip.kill()
            p_dump.kill()
            return False
        finally:
            p_gzip.stdout.close()

        if not self._wait_and_check(p_dump, p_gzip, identifier, db_name):
            return False

        logger.info(
            "[%s/%s] Uploaded to s3://%s/%s",
            identifier,
            db_name,
            self.s3_bucket,
            s3_key,
        )
        return True

    def _dump_to_local_storage(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        db_name: str,
        identifier: str,
    ) -> bool:
        out_dir = Path(self.local_backup_dir) / identifier
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"{db_name}-{self.timestamp}.sql.gz"
        logger.info("[%s/%s] Dumping -> %s", identifier, db_name, out_file)

        pipeline = self._start_pipeline(host, port, user, password, db_name, identifier)
        if not pipeline:
            return False
        p_dump, p_gzip = pipeline

        try:
            with out_file.open("wb") as f:
                while chunk := p_gzip.stdout.read(8192):
                    f.write(chunk)
        except Exception as exc:
            logger.error("[%s/%s] Local write failed: %s", identifier, db_name, exc)
            p_gzip.kill()
            p_dump.kill()
            return False
        finally:
            p_gzip.stdout.close()

        if not self._wait_and_check(p_dump, p_gzip, identifier, db_name):
            return False

        logger.info("[%s/%s] Saved to %s", identifier, db_name, out_file)
        return True
