from django.core.management import BaseCommand
from django.contrib.auth.models import User

from myauth.models import Profile


class Command(BaseCommand):
    def handle(self, *args, **options):
        users_without_profile = User.objects.filter(profile__isnull=True)
        for user in users_without_profile:
            profile = Profile.objects.create(user=user)
            self.stdout.write(self.style.SUCCESS(
                f'Created Profile object for user {user.username} (ID: {user.id}, Profile: {profile.id})'))
