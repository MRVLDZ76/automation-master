# management/commands/cleanup_task_logs.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from automation.models import TaskLog

class Command(BaseCommand):
    help = 'Deletes TaskLog entries older than 144 hours'

    def handle(self, *args, **kwargs):
        cutoff_date = timezone.now() - timedelta(hours=144)
        old_logs = TaskLog.objects.filter(timestamp__lt=cutoff_date)
        count = old_logs.count()
        old_logs.delete()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully deleted {count} task logs older than 72 hours')
        )
