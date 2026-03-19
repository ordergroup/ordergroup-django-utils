import sys

from django.core.management.base import BaseCommand

from og_django_utils.rds_backup.conf import get_config


class Command(BaseCommand):
    help = "Trigger a database backup ECS task on AWS."

    def add_arguments(self, parser):
        parser.add_argument(
            "--cluster",
            default=None,
            help="ECS cluster name (overrides settings.RDS_BACKUP['ECS_CLUSTER'])",
        )
        parser.add_argument(
            "--task-definition",
            default=None,
            help="ECS task definition (overrides settings.RDS_BACKUP['ECS_TASK_DEFINITION'])",
        )
        parser.add_argument(
            "--region",
            default=None,
            help="AWS region (overrides settings.RDS_BACKUP['AWS_REGION'])",
        )

    def handle(self, *args, **options):
        try:
            import boto3
        except ImportError:
            self.stderr.write(self.style.ERROR("boto3 is required but not found. Reinstall og-django-utils."))
            sys.exit(1)

        config = get_config()
        cluster = options["cluster"] or config["ECS_CLUSTER"]
        task_definition = options["task_definition"] or config["ECS_TASK_DEFINITION"]
        region = options["region"] or config["AWS_REGION"]

        if not cluster:
            self.stderr.write(
                self.style.ERROR("ECS cluster not configured. Set settings.RDS_BACKUP['ECS_CLUSTER'] or use --cluster")
            )
            sys.exit(1)

        ecs = boto3.client("ecs", region_name=region)

        self.stdout.write(f"Triggering ECS task: {task_definition} on cluster {cluster} ({region})")

        try:
            response = ecs.run_task(
                cluster=cluster,
                taskDefinition=task_definition,
                launchType="EC2",
            )
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"ECS run_task failed: {exc}"))
            sys.exit(1)

        tasks = response.get("tasks", [])
        if tasks:
            task_arn = tasks[0]["taskArn"]
            self.stdout.write(self.style.SUCCESS(f"Task started: {task_arn}"))
            self.stdout.write(f"View logs: aws logs tail /ecs/{task_definition} --follow --region {region}")
        else:
            failures = response.get("failures", [])
            self.stderr.write(self.style.ERROR(f"Task failed to start: {failures}"))
            sys.exit(1)
