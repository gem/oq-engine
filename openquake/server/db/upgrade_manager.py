# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2016-2025 GEM Foundation
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
import re
import time
import runpy
import urllib.request
import logging
import importlib
import sqlite3
from openquake.commonlib.dbapi import db


class DuplicatedVersion(RuntimeError):
    pass


class VersionTooSmall(RuntimeError):
    pass


class VersioningNotInstalled(RuntimeError):
    pass


CREATE_VERSIONING = '''\
CREATE TABLE %s(
version TEXT PRIMARY KEY,
scriptname TEXT NOT NULL,
executed TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
'''


class WrappedConnection(object):
    """
    This is an utility class that wraps a DB API-2 connection
    providing a couple of convenient features.

    1) it is possible to set a debug flag to print on stdout
       the executed queries;
    2) there is a .run method to run a query with a dedicated
       cursor; it returns the cursor, which can be iterated over

    :param conn: a DB API2-compatible connection
    """
    def __init__(self, conn, debug=False):
        self._conn = conn
        self.debug = debug

    def __getattr__(self, name):
        return getattr(self._conn, name)

    def run(self, templ, *args):
        """
        A simple utility to run SQL queries.

        :param templ: a query or query template
        :param args: the arguments (or the empty tuple)
        :returns: the DB API 2 cursor used to run the query
        """
        curs = self._conn.cursor()
        query = curs.mogrify(templ, args)
        if self.debug:
            print(query)
        curs.execute(query)
        return curs


# not used right now
def check_script(upgrade, conn, dry_run=True, debug=True):
    """
    An utility to debug upgrade scripts written in Python

    :param upgrade: upgrade procedure
    :param conn: a DB API 2 connection
    :param dry_run: if True, do not change the database
    :param debug: if True, print the queries which are executed
    """
    conn = WrappedConnection(conn, debug=debug)
    try:
        upgrade(conn)
    except Exception:
        conn.rollback()
        raise
    else:
        if dry_run:
            conn.rollback()
        else:
            conn.commit()


def apply_sql_script(conn, fname):
    """
    Apply the given SQL script to the database

    :param conn: a DB API 2 connection
    :param fname: full path to the creation script
    """
    sql = open(fname).read()
    try:
        # we cannot use conn.executescript which is non transactional
        for query in sql.split('\n\n'):
            conn.execute(query)
    except Exception:
        print('sqlite version =', sqlite3.sqlite_version)
        print(query)
        logging.error('Error executing %s' % fname)
        raise


# errors are not trapped on purpose, since transactions should be managed
# in client code
class UpgradeManager(object):
    r"""
    The package containing the upgrade scripts should contain an instance
    of the UpgradeManager called `upgrader` in the __init__.py file. It
    should also specify the initializations parameters

    :param upgrade_dir:
        the directory were the upgrade script reside
    :param version_table:
        the name of the versioning table (default revision_info)
    :param version_pattern:
        a regulation expression for the script version number (\d\d\d\d)
    """
    ENGINE_URL = 'https://github.com/gem/oq-engine/tree/master/'
    UPGRADES = 'openquake/server/db/schema/upgrades/'

    def __init__(self, upgrade_dir, version_table='revision_info',
                 version_pattern=r'\d\d\d\d', flag_pattern='(-slow|-danger)?'):
        self.upgrade_dir = upgrade_dir
        self.version_table = version_table
        self.version_pattern = version_pattern
        self.flag_pattern = flag_pattern
        self.pattern = r'^(%s)%s-([\w\-_]+)\.(sql|py)$' % (
            version_pattern, flag_pattern)
        self.upgrades_url = self.ENGINE_URL + self.UPGRADES
        if re.match(r'[\w_\.]+', version_table) is None:
            raise ValueError(version_table)
        self.starting_version = None  # will be updated after the run

    def _insert_script(self, script, conn):
        conn.cursor().execute(
            'INSERT INTO {} (version, scriptname) VALUES (?, ?)'.format(
                self.version_table),
            (script['version'], script['name']))

    def install_versioning(self, conn):
        """
        Create the version table into an already populated database
        and insert the base script.

        :param conn: a DB API 2 connection
        """
        logging.info('Creating the versioning table %s', self.version_table)
        conn.executescript(CREATE_VERSIONING % self.version_table)
        self._insert_script(self.read_scripts()[0], conn)

    def init(self, conn):
        """
        Create the version table and run the base script on an empty database.

        :param conn: a DB API 2 connection
        """
        base = self.read_scripts()[0]['fname']
        logging.info('Creating the initial schema from %s',  base)
        apply_sql_script(conn, os.path.join(self.upgrade_dir, base))
        self.install_versioning(conn)

    def upgrade(self, conn, skip_versions=()):
        '''
        Upgrade the database from the current version to the maximum
        version in the upgrade scripts.

        :param conn: a DBAPI 2 connection
        :param skip_versions: the versions to skip
        '''
        db_versions = self.get_db_versions(conn)
        self.starting_version = max(db_versions)
        to_skip = sorted(db_versions | set(skip_versions))
        scripts = self.read_scripts(None, None, to_skip)
        if not scripts:  # no new scripts to apply
            return []
        self.ending_version = max(s['version'] for s in scripts)
        return self._upgrade(conn, scripts)

    def _upgrade(self, conn, scripts):
        conn = WrappedConnection(conn)
        versions_applied = []
        for script in scripts:  # script is a dictionary
            fullname = os.path.join(self.upgrade_dir, script['fname'])
            logging.info('Executing %s', fullname)
            if script['ext'] == 'py':  # Python script with a upgrade(conn)
                globs = runpy.run_path(fullname)
                globs['upgrade'](conn)
                self._insert_script(script, conn)
            else:  # SQL script
                # notice that this prints the file name in case of error
                apply_sql_script(conn, fullname)
                self._insert_script(script, conn)
            versions_applied.append(script['version'])
        return versions_applied

    def check_versions(self, conn):
        """
        :param conn: a DB API 2 connection
        :returns: a message with the versions that will be applied or None
        """
        scripts = self.read_scripts(skip_versions=self.get_db_versions(conn))
        versions = [s['version'] for s in scripts]
        if versions:
            return ('Your database is not updated. You can update it by '
                    'running oq engine --upgrade-db which will process the '
                    'following new versions: %s' % versions)

    def get_db_versions(self, conn):
        """
        Get all the versions stored in the database as a set.

        :param conn: a DB API 2 connection
        """
        curs = conn.cursor()
        query = 'select version from {}'.format(self.version_table)
        try:
            curs.execute(query)
            return set(version for version, in curs.fetchall())
        except BaseException:
            raise VersioningNotInstalled('Run oq engine --upgrade-db')

    def parse_script_name(self, script_name):
        '''
        Parse a script name and return a dictionary with fields
        fname, name, version and ext (or None if the name does not match).

        :param name: name of the script
        '''
        match = re.match(self.pattern, script_name)
        if not match:
            return
        version, flag, name, ext = match.groups()
        return dict(fname=script_name, version=version, name=name,
                    flag=flag, ext=ext, url=self.upgrades_url + script_name)

    def read_scripts(self, minversion=None, maxversion=None, skip_versions=()):
        """
        Extract the upgrade scripts from a directory as a list of
        dictionaries, ordered by version.

        :param minversion: the minimum version to consider
        :param maxversion: the maximum version to consider
        :param skipversions: the versions to skip
        """
        scripts = []
        versions = {}  # a script is unique per version
        for scriptname in sorted(os.listdir(self.upgrade_dir)):
            match = self.parse_script_name(scriptname)
            if match:
                version = match['version']
                if version in skip_versions:
                    continue  # do not collect scripts already applied
                elif minversion and version <= minversion:
                    continue  # do not collect versions too old
                elif maxversion and version > maxversion:
                    continue  # do not collect versions too new
                try:
                    previousname = versions[version]
                except KeyError:  # no previous script with the same version
                    scripts.append(match)
                    versions[version] = scriptname
                else:
                    raise DuplicatedVersion(
                        'Duplicated versions {%s,%s}' %
                        (scriptname, previousname))
        return scripts

    def extract_upgrade_scripts(self):
        """
        Extract the OpenQuake upgrade scripts from the links in the GitHub page
        """
        link_pattern = r'>\s*{0}\s*<'.format(self.pattern[1:-1])
        page = urllib.request.urlopen(self.upgrades_url).read()
        for mo in re.finditer(link_pattern, page):
            scriptname = mo.group(0)[1:-1].strip()
            yield self.parse_script_name(scriptname)

    @classmethod
    def instance(cls, conn, pkg_name='openquake.server.db.schema.upgrades'):
        """
        Return an :class:`UpgradeManager` instance.

        :param conn: a DB API 2 connection
        :param str pkg_name: the name of the package with the upgrade scripts
        """
        try:
            # upgrader is an UpgradeManager instance defined in the __init__.py
            upgrader = importlib.import_module(pkg_name).upgrader
        except ImportError:
            raise SystemExit(
                'Could not import %s (not in the PYTHONPATH?)' % pkg_name)
        if not upgrader.read_scripts():
            raise SystemExit(
                'The upgrade_dir does not contain scripts matching '
                'the pattern %s' % upgrader.pattern)
        curs = conn.cursor()
        # check if there is already a versioning table
        curs.execute("SELECT name FROM sqlite_master "
                     "WHERE name=%r" % upgrader.version_table)
        versioning_table = curs.fetchall()
        # if not, run the base script and create the versioning table
        if not versioning_table:
            upgrader.init(conn)
            conn.commit()
        return upgrader


def upgrade_db(conn=None, pkg_name='openquake.server.db.schema.upgrades',
               skip_versions=()):
    """
    Upgrade a database by running several scripts in a single transaction.

    :param conn: a DB API 2 connection (if None use dbapi.db.conn)
    :param str pkg_name: the name of the package with the upgrade scripts
    :param list skip_versions: the versions to skip
    :returns: the version numbers of the new scripts applied the database
    """
    if conn is None:
        conn = db.conn
    upgrader = UpgradeManager.instance(conn, pkg_name)
    t0 = time.time()
    # run the upgrade scripts
    try:
        versions_applied = upgrader.upgrade(conn, skip_versions)
    except Exception:
        conn.rollback()
        raise
    else:
        conn.commit()
    if versions_applied:
        logging.info('Upgrade completed in %s seconds', time.time() - t0)
    return versions_applied


def db_version(conn, pkg_name='openquake.server.db.schema.upgrades'):
    """
    :param conn: a DB API 2 connection
    :param str pkg_name: the name of the package with the upgrade scripts
    :returns: the current version of the database
    """
    upgrader = UpgradeManager.instance(conn, pkg_name)
    return max(upgrader.get_db_versions(conn))


def what_if_I_upgrade(conn, pkg_name='openquake.server.db.schema.upgrades',
                      extract_scripts='extract_upgrade_scripts'):
    """
    :param conn:
        a DB API 2 connection
    :param str pkg_name:
        the name of the package with the upgrade scripts
    :param extract_scripts:
        name of the method to extract the scripts
    """
    msg_safe_ = '\nThe following scripts can be applied safely:\n%s'
    msg_slow_ = '\nPlease note that the following scripts could be slow:\n%s'
    msg_danger_ = ('\nPlease note that the following scripts are potentially '
                   'dangerous and could destroy your data:\n%s')
    upgrader = UpgradeManager.instance(conn, pkg_name)
    applied_versions = upgrader.get_db_versions(conn)
    current_version = max(applied_versions)
    slow = []
    danger = []
    safe = []
    for script in getattr(upgrader, extract_scripts)():
        url = script['url']
        if script['version'] in applied_versions:
            continue
        elif script['version'] <= current_version:
            # you cannot apply a script with a version number lower than the
            # current db version: ensure that upgrades are strictly incremental
            raise VersionTooSmall(
                'Your database is at version %s but you want to apply %s??'
                % (current_version, script['fname']))
        elif script['flag'] == '-slow':
            slow.append(url)
        elif script['flag'] == '-danger':
            danger.append(url)
        else:  # safe script
            safe.append(url)

    if not safe and not slow and not danger:
        return 'Your database is already updated at version %s.' % \
            current_version

    header = 'Your database is at version %s.' % current_version
    msg_safe = msg_safe_ % '\n'.join(safe)
    msg_slow = msg_slow_ % '\n'.join(slow)
    msg_danger = msg_danger_ % '\n'.join(danger)
    msg = header + (msg_safe if safe else '') + (msg_slow if slow else '') \
        + (msg_danger if danger else '')
    msg += ('\nClick on the links if you want to know what exactly the '
            'scripts are doing.')
    if slow:
        msg += ('\nEven slow script can be fast if your database is small or'
                ' the upgrade affects tables that are empty.')
    if danger:
        msg += ('\nEven dangerous scripts are fine if they '
                'affect empty tables or data you are not interested in.')
    return msg


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    path = sys.argv[1]
    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)
    conn = sqlite3.connect(path)
    upgrade_db(conn)
