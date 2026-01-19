import os
import pytest
from django.contrib.auth import get_user_model

# pytest-playwright starts an asyncio event loop at session startup.
# Django 4+ forbids synchronous ORM/database operations when an event loop
# is already running and raises SynchronousOnlyOperation during test DB setup.
# This flag explicitly allows sync Django DB usage in this test environment.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


@pytest.fixture
def application_mode(settings, request):
    mode = request.param
    settings.APPLICATION_MODE = mode
    return mode


@pytest.fixture
def test_credentials():
    return {
        "username": "test_user",
        "password": "password123",
        "email": "test@user.com",
    }


@pytest.fixture
def user(db, application_mode, test_credentials, request):
    level = request.param

    User = get_user_model()
    user = User.objects.create_user(
        username=test_credentials["username"],
        email=test_credentials["email"],
        password=test_credentials["password"],
    )

    profile = user.profile
    profile.level = level
    profile.save()

    return user


@pytest.fixture
def authenticated_session(db, user):
    from django.test import Client
    client = Client()
    client.force_login(user)
    session = client.session
    session.save()
    return session.session_key


@pytest.fixture
def authenticated_page(page, live_server, authenticated_session, application_mode):
    page.context.clear_cookies()
    page.context.add_cookies([{
        "name": "sessionid",
        "value": authenticated_session,
        "url": live_server.url,
    }])
    page.goto(f"{live_server.url}/engine/")
    return page


@pytest.fixture
def ui_logged_in_page(page, live_server, user, test_credentials, application_mode):
    page.context.clear_cookies()
    page.goto(f"{live_server.url}/engine/")

    page.get_by_label("Username").fill(test_credentials["username"])
    page.get_by_label("Password").fill(test_credentials["password"])
    page.get_by_role("button", name="Log in").click()

    page.wait_for_url(f"{live_server.url}/engine/")
    return page
