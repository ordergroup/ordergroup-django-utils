import logging
import os
import shutil
import subprocess
import time
from pathlib import Path

from django.db import connections

from .conf import get_config, get_db_credentials

logger = logging.getLogger("og.db_backup")


class BackupManager:
    """PostgreSQL backup manager that reads configuration from Django settings.

    Runs pg_dump | gzip pipeline and saves output to S3 or local file.
    Uses Django's database connection for database discovery.
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

    @property
    def s3_client(self):
        if self._s3_client is None:
            try:
                import boto3
            except ImportError as exc:
                raise ImportError(
                    "boto3 is required for S3 uploads. "
                    "Install with: pip install og-django-utils[db_backup]"
                ) from exc
            self._s3_client = boto3.client("s3", region_name=self.region)
        return self._s3_client

    # ------------------------------------------------------------------
    # Database discovery via Django connection
    # ------------------------------------------------------------------

    def get_databases(self, database_alias: str = "default") -> list[str]:
        """List non-template, connectable databases using Django's connection."""
        connection = connections[database_alias]
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT datname FROM pg_database "
                "WHERE datistemplate = false "
                "AND datallowconn = true "
                "ORDER BY datname"
            )
            all_dbs = [row[0] for row in cursor.fetchall()]
        return [db for db in all_dbs if db not in self.db_exclude]

    # ------------------------------------------------------------------
    # Dump pipeline
    # ------------------------------------------------------------------

    def _check_pg_dump(self) -> None:
        """Verify pg_dump binary is available."""
        if not shutil.which("pg_dump"):
            raise FileNotFoundError(
                "pg_dump not found. Install postgresql-client: "
                "apt install postgresql-client / brew install postgresql"
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
        """Start pg_dump | gzip pipeline."""
        env = {**os.environ, "PGPASSWORD": password}
        pg_dump_cmd = [
            "pg_dump",
            "--no-owner",
            "--clean",
            "--if-exists",
            "-h", host,
            "-p", str(port),
            "-U", user,
            "-d", db_name,
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
        """Wait for both processes and check exit codes."""
        p_gzip.wait()
        p_dump.wait()

        errors = self._collect_errors([("pg_dump", p_dump), ("gzip", p_gzip)])
        if errors:
            for step, rc, msg in errors:
                logger.error(
                    "[%s/%s] %s failed (rc=%d): %s",
                    identifier, db_name, step, rc, msg,
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

    # ------------------------------------------------------------------
    # Dump to S3
    # ------------------------------------------------------------------

    def _dump_to_s3(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        db_name: str,
        identifier: str,
    ) -> bool:
        """Stream pg_dump | gzip directly to S3."""
        s3_key = f"{self.s3_prefix}/{identifier}/{db_name}-{self.timestamp}.sql.gz"
        logger.info(
            "[%s/%s] Dumping -> s3://%s/%s",
            identifier, db_name, self.s3_bucket, s3_key,
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
            identifier, db_name, self.s3_bucket, s3_key,
        )
        return True

    # ------------------------------------------------------------------
    # Dump to local file
    # ------------------------------------------------------------------

    def _dump_to_local(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        db_name: str,
        identifier: str,
    ) -> bool:
        """Stream pg_dump | gzip to a local file."""
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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def dump_database(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        db_name: str,
        identifier: str,
    ) -> bool:
        """Run pg_dump | gzip and save to S3 or local file."""
        if self.use_s3:
            return self._dump_to_s3(host, port, user, password, db_name, identifier)
        return self._dump_to_local(host, port, user, password, db_name, identifier)

    def backup_databases(
        self,
        database_alias: str = "default",
        all_databases: bool = False,
    ) -> int:
        """Backup databases using credentials from Django settings.

        Returns 0 on success, 1 if all backups failed.
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
            self.results[key] = self.dump_database(
                host, port, user, password, db_name, identifier,
            )

        elapsed = time.monotonic() - start
        total = len(self.results)
        succeeded = sum(1 for v in self.results.values() if v)
        failed = total - succeeded

        logger.info(
            "Done in %.1fs — %d/%d succeeded, %d failed",
            elapsed, succeeded, total, failed,
        )

        if failed:
            logger.warning(
                "Failed: %s",
                ", ".join(k for k, v in self.results.items() if not v),
            )

        if total > 0 and failed == total:
            return 1
        return 0
