from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings

from og_django_utils.db_backup.conf import get_config, get_db_credentials
from og_django_utils.db_backup.constants import DEFAULT_EXCLUDE


class TestGetConfig:
    def test_defaults(self):
        config = get_config()
        assert config["S3_BUCKET"] == ""
        assert config["S3_PREFIX"] == "dumps"
        assert config["S3_STORAGE_CLASS"] == "STANDARD_IA"
        assert config["LOCAL_BACKUP_DIR"] == "./backups"
        assert config["DB_EXCLUDE"] == DEFAULT_EXCLUDE
        assert config["AWS_REGION"] == "eu-central-1"
        assert config["ECS_TASK_DEFINITION"] == "db-ops-backup"

    @override_settings(DB_BACKUP={
        "S3_BUCKET": "test-bucket",
        "IDENTIFIER": "myapp-prod",
        "ECS_CLUSTER": "prod-cluster",
    })
    def test_from_django_settings(self):
        config = get_config()
        assert config["S3_BUCKET"] == "test-bucket"
        assert config["IDENTIFIER"] == "myapp-prod"
        assert config["ECS_CLUSTER"] == "prod-cluster"
        assert config["S3_PREFIX"] == "dumps"

    @override_settings(DB_BACKUP={"S3_BUCKET": "from-settings"})
    def test_settings_take_priority_over_env(self):
        with patch.dict("os.environ", {"BACKUP_S3_BUCKET": "from-env"}):
            config = get_config()
            assert config["S3_BUCKET"] == "from-settings"

    def test_env_var_fallback(self):
        with patch.dict("os.environ", {"BACKUP_S3_BUCKET": "from-env"}):
            config = get_config()
            assert config["S3_BUCKET"] == "from-env"


class TestGetDbCredentials:
    @override_settings(DATABASES={
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": "db.example.com",
            "PORT": "5433",
            "USER": "admin",
            "PASSWORD": "secret",
            "NAME": "myapp_db",
        }
    })
    def test_extracts_credentials(self):
        creds = get_db_credentials("default")
        assert creds["host"] == "db.example.com"
        assert creds["port"] == 5433
        assert creds["user"] == "admin"
        assert creds["password"] == "secret"
        assert creds["name"] == "myapp_db"

    @override_settings(DATABASES={
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": "",
            "PORT": "",
            "USER": "postgres",
            "PASSWORD": "",
            "NAME": "testdb",
        }
    })
    def test_defaults_for_empty_host_port(self):
        creds = get_db_credentials("default")
        assert creds["host"] == "localhost"
        assert creds["port"] == 5432

    def test_missing_alias_raises(self):
        with pytest.raises(ValueError, match="not found"):
            get_db_credentials("nonexistent")

    @override_settings(DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    })
    def test_non_postgresql_raises(self):
        with pytest.raises(ValueError, match="only PostgreSQL"):
            get_db_credentials("default")

    @override_settings(DATABASES={
        "default": {
            "ENGINE": "django.contrib.gis.db.backends.postgis",
            "HOST": "localhost",
            "PORT": "5432",
            "USER": "geo",
            "PASSWORD": "pass",
            "NAME": "geodb",
        }
    })
    def test_postgis_engine_works(self):
        creds = get_db_credentials("default")
        assert creds["user"] == "geo"


class TestBackupManager:
    @override_settings(
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "HOST": "localhost",
                "PORT": "5432",
                "USER": "postgres",
                "PASSWORD": "postgres",
                "NAME": "testdb",
            }
        },
        DB_BACKUP={"IDENTIFIER": "test-app"},
    )
    @patch("shutil.which", return_value=None)
    def test_raises_if_pg_dump_missing(self, mock_which):
        from og_django_utils.db_backup.manager import BackupManager

        manager = BackupManager()
        with pytest.raises(FileNotFoundError, match="pg_dump not found"):
            manager.backup_databases()

    @override_settings(DB_BACKUP={"S3_BUCKET": "my-bucket"})
    def test_s3_mode_detected(self):
        from og_django_utils.db_backup.manager import BackupManager

        manager = BackupManager()
        assert manager.use_s3 is True

    @override_settings(DB_BACKUP={})
    def test_local_mode_detected(self):
        from og_django_utils.db_backup.manager import BackupManager

        manager = BackupManager()
        assert manager.use_s3 is False

    def test_overrides_in_constructor(self):
        from og_django_utils.db_backup.manager import BackupManager

        manager = BackupManager(S3_BUCKET="override-bucket", IDENTIFIER="custom-id")
        assert manager.s3_bucket == "override-bucket"
        assert manager.identifier == "custom-id"
        assert manager.use_s3 is True

    def test_s3_client_requires_boto3(self):
        from og_django_utils.db_backup.manager import BackupManager

        manager = BackupManager(S3_BUCKET="test")
        with patch.dict("sys.modules", {"boto3": None}):
            pass


class TestTriggerDbBackupCommand:
    @override_settings(DB_BACKUP={
        "ECS_CLUSTER": "test-cluster",
        "ECS_TASK_DEFINITION": "test-task",
        "AWS_REGION": "eu-central-1",
    })
    def test_trigger_calls_ecs_run_task(self):
        from django.core.management import call_command

        mock_ecs = MagicMock()
        mock_ecs.run_task.return_value = {
            "tasks": [{"taskArn": "arn:aws:ecs:eu-central-1:123:task/abc"}],
            "failures": [],
        }

        mock_boto3 = MagicMock()
        mock_boto3.client.return_value = mock_ecs

        with patch.dict("sys.modules", {"boto3": mock_boto3}):
            call_command("trigger_db_backup")

        mock_boto3.client.assert_called_once_with("ecs", region_name="eu-central-1")
        mock_ecs.run_task.assert_called_once_with(
            cluster="test-cluster",
            taskDefinition="test-task",
            launchType="EC2",
        )
