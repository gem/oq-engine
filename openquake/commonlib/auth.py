"""Authentication values shared by the WebUI views and the internal API."""

import os
import sys
import secrets

from openquake.baselib import config, is_server_installation

# default key of the old configuration files: since it is public, it is
# treated as no key
PUBLIC_KEY = 'changeme'


def get_api_key(environ=os.environ):
    """
    :returns:
        the key of the internal API, from the OQ_API_KEY environment variable
        or from the authkey in the [webapi] section of openquake.cfg; an empty
        string, meaning that the internal API is closed, if no key is set or
        if the key is the public "changeme"
    """
    key = environ.get('OQ_API_KEY') or config.webapi.get('authkey') or ''
    return '' if key == PUBLIC_KEY else key


API_KEY = get_api_key()
if not API_KEY and (any('pytest' in arg for arg in sys.argv)
                    or os.environ.get('OQ_TEST')):
    # the tests call the internal API of the WebUI servers they start, which
    # inherit the environment and therefore this random key
    API_KEY = os.environ['OQ_API_KEY'] = secrets.token_urlsafe(32)


def api_key_error():
    """
    :returns:
        an error message if the key of the internal API is not set in a
        server installation, where the processes of the users reach the WebUI
        via the internal API (install.py generates the key); None otherwise
    """
    if is_server_installation() and not API_KEY:
        return ('The key of the internal API is not set: set the authkey in '
                'the [webapi] section of openquake.cfg (or the OQ_API_KEY '
                'environment variable) to a random string, e.g. the output '
                'of python3 -c "import secrets; '
                'print(secrets.token_urlsafe(32))"; the public '
                f'"{PUBLIC_KEY}" is not accepted')
