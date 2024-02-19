import secrets
import string
import logging
from django.http import HttpRequest
from django.core.management.base import BaseCommand
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
from django.conf import settings


logger = logging.getLogger(__name__)


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
        if User.objects.filter(username=username).exists():
            logger.error(f'The username "{username}" is already taken!')
            exit(1)
        logger.info(f'Creating normal user: {username}')
        user = User.objects.create_user(
            username, password=password, email=email)
        user.save()
        logger.info(f'Sending reset password email to: {user.email}')
        form = PasswordResetForm({'email': user.email})
        assert form.is_valid()
        request = HttpRequest()
        request.META['SERVER_NAME'] = settings.SERVER_NAME
        request.META['SERVER_PORT'] = settings.SERVER_PORT
        if settings.USE_REVERSE_PROXY:
            if settings.USE_HTTPS:
                request.META['SERVER_PORT'] = '443'
            else:
                request.META['SERVER_PORT'] = '80'
        else:
            request.META['SERVER_PORT'] = settings.SERVER_PORT
        if settings.APPLICATION_MODE.upper() == 'AELO':
            password_reset_subject = (
                'registration/normal_user_creation_email_subject_aelo.txt')
            email_template_name = (
                'registration/normal_user_creation_email_aelo.txt')
        else:
            password_reset_subject = (
                'registration/normal_user_creation_email_subject.txt')
            email_template_name = (
                'registration/normal_user_creation_email.txt')
        form.save(
            domain_override=(settings.SERVER_NAME
                             if settings.USE_REVERSE_PROXY else None),
            request=request,
            use_https=settings.USE_HTTPS,
            from_email=settings.EMAIL_HOST_USER,
            subject_template_name=password_reset_subject,
            email_template_name=email_template_name)
