import mock


class MultiMock(object):
    """
    Context-managed multi-mock object. This is useful if you need to mock
    multiple things at once. So instead of creating individual patch+mock
    objects for each, you can define them basically as a dictionary. You can
    also use the mock context managers without having to nest `with`
    statements.

    Example usage:

    .. code-block:: python

        # First, define your mock targets as a dictionary.
        # The value of each item is the path to the function/method you wish to
        # mock. The key is basically a shortcut to the mock.
        mocks = {
            'touch': 'openquake.engine.engine.touch_log_file',
            'job': 'openquake.engine.engine.haz_job_from_file',
        }
        multi_mock = MultiMock(**mocks)

        # To start mocking, start the context manager using `with`:
        # with multi_mock:
        with multi_mock:
            # You can mock return values, for example, just as you would with
            # any other Mock object:
            multi_mock['job'].return_value = 'foo'

            # call the function under test which will calls the mocked
            # functions
            engine.run_hazard('job.ini', 'debug', 'oq.log', ['geojson'])

            # To test the mocks, you can simply access each mock from
            # `multi_mock` like a dict:
            assert multi_mock['touch'].call_count == 1
    """

    def __init__(self, **mocks):
        # dict of mock names -> mock paths
        self._mocks = mocks
        self.active_patches = {}
        self.active_mocks = {}

    def __enter__(self):
        for key, value in self._mocks.iteritems():
            the_patch = mock.patch(value)
            self.active_patches[key] = the_patch
            self.active_mocks[key] = the_patch.start()
        return self

    def __exit__(self, *args):
        for each_mock in self.active_mocks.itervalues():
            each_mock.stop()
        for each_patch in self.active_patches.itervalues():
            each_patch.stop()

    def __iter__(self):
        return self.active_mocks.itervalues()

    def __getitem__(self, key):
        return self.active_mocks.get(key)
