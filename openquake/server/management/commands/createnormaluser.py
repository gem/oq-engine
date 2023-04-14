import secrets
import string
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Create a normal user'

    def add_arguments(self, parser):
        parser.add_argument(
            'username', type=str,
            help='The username that will be assigned to the new user')
        parser.add_argument(
            'email', type=str,
            help='The email that will be assigned to the user')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        email = kwargs['email']
        # secure password, like '4x]>@;4)'
        password = ''.join((
            secrets.choice(
                string.ascii_letters + string.digits + string.punctuation)
            for i in range(8)))
        # by default a user is not superuser and not staff
        User = get_user_model()
        user = User.objects.create_user(
            username, password=password, email=email)
        user.save()
