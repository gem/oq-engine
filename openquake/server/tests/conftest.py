# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2026 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import pytest
import glob
import shutil
import pathlib
import subprocess
import tempfile
import zipfile
from django.contrib.auth import get_user_model
from openquake.baselib import config
from openquake.server.tests.views_test import start_uvicorn, stop_uvicorn

# pytest-playwright starts an asyncio event loop at session startup.
# Django 4+ forbids synchronous ORM/database operations when an event loop
# is already running and raises SynchronousOnlyOperation during test DB setup.
# This flag explicitly allows sync Django DB usage in this test environment.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")


def copy_from_templates_if_needed(tmpldir, ext):
    fnames = glob.glob(f'{tmpldir}/*{ext}')
    for fname in fnames:
        stripped = fname[:-len(ext)]
        # i.e. email_subject.txt.aelo.templ -> email_subject.txt'
        if not os.path.exists(stripped):
            shutil.copy(fname, stripped)


def _download_server_data(data_dir):
    """Download the files used by the server integration tests."""
    base_url = 'https://downloads.openquake.org/test_data'
    files = ('worldcities.csv', 'countries_info.csv',
             'World_Adm1_updated.gpkg')
    for name in files:
        target = data_dir / name
        if not target.exists():
            subprocess.run(
                ['wget', f'{base_url}/{name}', '-O', str(target)],
                check=True)

    fonts_dir = data_dir / 'fonts'
    if not any(fonts_dir.glob('NotoSans*-Regular.ttf')):
        archive_path = data_dir / 'fonts.zip'
        if not archive_path.exists():
            subprocess.run(
                ['wget', f'{base_url}/fonts.zip', '-O', str(archive_path)],
                check=True)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(data_dir)


def _configure_server_data(data_dir):
    """Configure the downloaded data for this process and its children."""
    fd, cfg_path = tempfile.mkstemp(prefix='oq-server-tests-', suffix='.cfg')
    os.close(fd)
    paths = {
        'world_cities_file': data_dir / 'worldcities.csv',
        'countries_info_file': data_dir / 'countries_info.csv',
        'admin1_boundaries_file': data_dir / 'World_Adm1_updated.gpkg',
        'fonts_dir': data_dir / 'fonts',
    }
    with open(cfg_path, 'w') as cfg:
        cfg.write('[directory]\n')
        for name, path in paths.items():
            cfg.write(f'{name} = {path}\n')
    for name, path in paths.items():
        config.directory[name] = str(path)
    return cfg_path


_server_cfg_path = None
_server_old_cfg_path = None


def _prepare_server_data():
    global _server_cfg_path, _server_old_cfg_path
    if _server_cfg_path is not None:
        return
    data_dir = pathlib.Path(__file__).parent / 'data'
    data_dir.mkdir(exist_ok=True)
    _download_server_data(data_dir)
    _server_cfg_path = _configure_server_data(data_dir)
    _server_old_cfg_path = os.environ.get('OQ_CONFIG_FILE')
    os.environ['OQ_CONFIG_FILE'] = _server_cfg_path


def pytest_configure(config):
    """Prepare paths before unittest classes or worker processes start."""
    _prepare_server_data()


@pytest.fixture(scope="session", autouse=True)
def server_test_data():
    """Make server test data available, downloading only missing files."""
    _prepare_server_data()
    yield
    if _server_old_cfg_path is None:
        os.environ.pop('OQ_CONFIG_FILE', None)
    else:
        os.environ['OQ_CONFIG_FILE'] = _server_old_cfg_path
    pathlib.Path(_server_cfg_path).unlink(missing_ok=True)


@pytest.fixture(scope="session", autouse=True)
def migrate_before_tests(server_test_data):
    """
    Generate registration files before running migrations (if needed),
    then load data fixtures
    """
    serverdir = pathlib.Path(__file__).parent.parent
    appmode = os.environ.get('OQ_APPLICATION_MODE', '').upper()
    # generate the files needed for user registration and email notifications
    ext = (f'.{appmode.lower()}.tmpl'
           if appmode in ('AELO', 'IMPACT')
           else '.default.tmpl')
    copy_from_templates_if_needed(serverdir / 'templates/registration', ext)
    # the tests share the engine DB (there is no pytest-django test DB), so
    # make sure it is migrated before the server process connects to it
    subprocess.run([sys.executable, serverdir / 'manage.py', 'migrate'],
                   check=True)
    if appmode in ['AELO', 'IMPACT']:
        # load cookie-related fixtures
        js = (serverdir / 'fixtures/0001_cookie_consent_required_'
                          'plus_hide_cookie_bar.json')
        subprocess.run([sys.executable, serverdir / 'manage.py', 'loaddata', js],
                       check=True)
    yield


@pytest.fixture(scope="session")
def django_db_setup():
    """
    Use the engine DB directly (no pytest-django test DB): the server runs
    in a separate process and must see the same users and sessions as the
    test process.
    """
    pass


@pytest.fixture
def application_mode(settings, request):
    mode = request.param
    settings.APPLICATION_MODE = mode
    return mode


@pytest.fixture
def default_usgs_id(settings, request):
    mode = request.param
    settings.IMPACT_DEFAULT_USGS_ID = mode
    return mode


@pytest.fixture
def test_credentials():
    return {
        "username": "test_user",
        "password": "password123",
        "email": "test@user.com",
    }


@pytest.fixture
def user(django_db_blocker, application_mode, test_credentials, request):
    level = request.param

    # use the engine DB directly (no pytest-django test DB) so that the
    # server process can see the user and the session
    django_db_blocker.unblock()
    User = get_user_model()
    user, _ = User.objects.get_or_create(
        username=test_credentials["username"],
        defaults={"email": test_credentials["email"]})
    user.set_password(test_credentials["password"])
    user.email = test_credentials["email"]
    user.save()

    profile = user.profile
    profile.level = level
    profile.save()

    return user


@pytest.fixture
def authenticated_session(django_db_blocker, user):
    from django.test import Client
    django_db_blocker.unblock()
    client = Client()
    client.force_login(user)
    session = client.session
    session.save()
    return session.session_key


@pytest.fixture
def authenticated_page(page, authenticated_session, application_mode):
    server, thread, client = start_uvicorn()
    try:
        page.context.clear_cookies()
        page.context.add_cookies([{
            "name": "sessionid",
            "value": authenticated_session,
            "url": client.base_url,
        }])
        page.goto(f"{client.base_url}/engine/")
        yield page
    finally:
        stop_uvicorn(server, thread)


@pytest.fixture
def ui_logged_in_page(
        page, live_server, user, test_credentials, application_mode):
    page.context.clear_cookies()
    page.goto(f"{live_server.url}/engine/")

    page.get_by_label("Username").fill(test_credentials["username"])
    page.get_by_label("Password").fill(test_credentials["password"])
    page.get_by_role("button", name="Log in").click()

    page.wait_for_url(f"{live_server.url}/engine/")
    return page


def pytest_addoption(parser):
    parser.addoption(
        "--skip-abort-jobs",
        action="store_true",
        default=False,
        help="Skip aborting jobs after test execution."
    )
    parser.addoption(
        "--skip-remove-jobs",
        action="store_true",
        default=False,
        help="Skip removing jobs after test execution."
    )


@pytest.fixture
def should_abort_job(request):
    """
    Returns True by default, False if --skip-abort-jobs is passed.
    """
    return not request.config.getoption("--skip-abort-jobs")


@pytest.fixture
def should_remove_job(request):
    """
    Returns True by default, False if --skip-remove-jobs is passed.
    """
    return not request.config.getoption("--skip-remove-jobs")
