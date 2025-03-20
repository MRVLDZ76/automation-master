# management/commands/fix_task_completion.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from automation.models import ScrapingTask
from django.db.models import Q

class Command(BaseCommand):
    help = 'Checks and fixes task completion timestamps'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Fix inconsistent task statuses',
        )
        parser.add_argument(
            '--report',
            action='store_true',
            help='Generate a report of inconsistent tasks',
        )

    def handle(self, *args, **options):
        # Find tasks with status DONE but no completion time
        inconsistent_tasks = ScrapingTask.objects.filter(
            Q(status='DONE', completed_at__isnull=True) |
            Q(status='COMPLETED', completed_at__isnull=True)
        )

        if options['report']:
            self.stdout.write(self.style.WARNING(f'Found {inconsistent_tasks.count()} inconsistent tasks:'))
            for task in inconsistent_tasks:
                self.stdout.write(f'Task ID: {task.id} | Status: {task.status} | Created: {task.created_at}')

        if options['fix']:
            now = timezone.now()
            updated_count = inconsistent_tasks.update(completed_at=now)
            self.stdout.write(self.style.SUCCESS(f'Updated {updated_count} tasks with completion time'))

        # Preventive check for in-progress tasks
        old_in_progress = ScrapingTask.objects.filter(
            status='IN_PROGRESS',
            created_at__lt=timezone.now() - timezone.timedelta(days=7)
        )

        if old_in_progress.exists():
            self.stdout.write(self.style.WARNING(
                f'Found {old_in_progress.count()} tasks stuck in IN_PROGRESS status for over 7 days'
            ))
            for task in old_in_progress:
                self.stdout.write(f'Task ID: {task.id} | Created: {task.created_at}')

# Generate a report only
#python manage.py fix_task_completion --report

# Fix inconsistent tasks
#python manage.py fix_task_completion --fix

# Both report and fix
#python manage.py fix_task_completion --report --fix
