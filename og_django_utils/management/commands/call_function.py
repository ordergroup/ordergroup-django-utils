from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string


class Command(BaseCommand):
    help = 'Enables you to call any function available in the project.'

    def add_arguments(self, parser):
        parser.add_argument('function_path', type=str)

    def handle(self, *args, **options):
        function_path = options['function_path']
        func = import_string(function_path)
        return func()
