import os
from django.core.management.base import BaseCommand
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Create initial admin user from environment variables'

    def handle(self, *args, **options):
        email = os.getenv('INITIAL_ADMIN_EMAIL')
        password = os.getenv('INITIAL_ADMIN_PASSWORD')

        if not email or not password:
            self.stdout.write(
                self.style.WARNING(
                    'INITIAL_ADMIN_EMAIL and INITIAL_ADMIN_PASSWORD must be set in environment variables.'
                )
            )
            return

        # Check if admin already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'Admin user with email {email} already exists. Skipping.')
            )
            return

        # Create admin user
        User.objects.create_superuser(email=email, password=password)
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created admin user: {email}')
        )
