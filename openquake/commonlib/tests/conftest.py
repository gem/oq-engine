# -*- coding: utf-8 -*-
"""Fixtures for tests that use the local database directly."""

import os


# These tests exercise datastore and logging behaviour, not the database service
# transport.  Force the single-user dispatcher path unless the caller has
# explicitly selected another database.
os.environ.setdefault('OQ_DATABASE', '127.0.0.1')
