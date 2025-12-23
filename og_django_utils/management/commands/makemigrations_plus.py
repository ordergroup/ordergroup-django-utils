# -*- coding: utf-8 -*-
import os

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Runs makemigrations and adds them to the git repository.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING('Running makemigrations...'))
        call_command('makemigrations', interactive=True)
        self.stdout.write(self.style.MIGRATE_HEADING('Done, adding migrations to git...'))
        os.system("git ls-files -co --exclude-standard | grep '.*/migrations/.*py' | xargs git add")
        self.stdout.write(self.style.MIGRATE_HEADING('Finished.'))
