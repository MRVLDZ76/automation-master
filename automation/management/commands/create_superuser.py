from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model() 

class Command(BaseCommand):
    help = 'Creates a superuser'

    def handle(self, *args, **options):
        username = 'EdisonValdez'
        email = 'iancasillasbuffon@gmail.com'   
        password = 'Thesecret1'

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User "{username}" already exists'))
            return

        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )

        self.stdout.write(self.style.SUCCESS(f'Successfully created superuser "{username}"'))

