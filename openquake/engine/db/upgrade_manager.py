import os
import re
import runpy
import importlib
from openquake.engine import logs


class DuplicatedVersion(RuntimeError):
    pass


class VersioningNotInstalled(RuntimeError):
    pass

CREATE_VERSIONING = '''\
CREATE TABLE %s(
version TEXT PRIMARY KEY,
scriptname TEXT NOT NULL,
executed TIMESTAMP NOT NULL DEFAULT now()
);
'''


def apply_sql_script(conn, fname):
    """
    Apply the given SQL script to the database

    :param conn: a DB API 2 connection
    :param fname: full path to the creation script
    """
    sql = open(fname).read()
    try:
        conn.cursor().execute(sql)
    except:
        logs.LOG.error('Error executing %s' % fname)
        raise


# errors are not trapped on purpose, since transactions should be managed
# in client code
class UpgradeManager(object):
    """
    The package containing the upgrade scripts should contain an instance
    of the UpgradeManager called `upgrader` in the __init__.py file. It
    should also specify the initializations parameters

    :param version_pattern:
        a regulation expression for the script version number
    :param upgrade_dir:
        the directory were the upgrade script reside
    :param version_table:
        the name of the table containing the versions
    """
    def __init__(self, version_pattern, upgrade_dir,
                 version_table='db_version'):
        self.upgrade_dir = upgrade_dir
        self.version_pattern = version_pattern
        self.pattern = r'^(%s[rs]?)-([\w\-_]+)\.(sql|py)$' % version_pattern
        self.version_table = version_table
        if re.match('[\w_\.]+', version_table) is None:
            raise ValueError(version_table)
        self.version = None  # will be updated after the run
        self.starting_version = None  # will be updated after the run

    def _insert_script(self, script, conn):
        conn.cursor().execute(
            'INSERT INTO {} VALUES (%s, %s)'.format(self.version_table),
            (script['version'], script['name']))

    def install_versioning(self, conn):
        """
        Create the version table into an already populated database
        and insert the base script.

        :param conn: a DB API 2 connection
        """
        conn.cursor().execute(CREATE_VERSIONING % self.version_table)
        self._insert_script(self.read_scripts()[0], conn)

    def init(self, conn):
        """
        Create the version table and run the base script on an empty database.
        """
        base = self.read_scripts()[0]['fname']
        apply_sql_script(conn, os.path.join(self.upgrade_dir, base))
        self.install_versioning(conn)

    def upgrade(self, conn):
        '''
        Upgrade the database from the current version to the maximum
        version in the upgrade scripts.
        '''
        db_versions = self.get_db_versions(conn)
        self.starting_version = sorted(db_versions)[-1]  # the highest version
        self.ending_version = self.get_max_version()
        if self.starting_version == self.ending_version:
            logs.LOG.warn('The database is updated at version %s. '
                          'Nothing to do.', self.starting_version)
            return
        logs.LOG.warn('The database is at version %s. Upgrading to version '
                      '%s.', self.starting_version, self.ending_version)
        self._from_to_version(conn, self.starting_version, self.ending_version,
                              db_versions=db_versions)

    def _from_to_version(self, conn, from_version, to_version, db_versions):
        scripts = self.read_scripts(from_version, to_version, db_versions)
        for script in scripts:  # script is a dictionary
            fullname = os.path.join(self.upgrade_dir, script['fname'])
            logs.LOG.warn('Executing %s', fullname)
            if script['ext'] == 'py':  # Python script with a upgrade(conn)
                runpy.run_path(fullname)['upgrade'](conn)
                self._insert_script(script, conn)
            else:  # SQL script
                # notice that this prints the file name in case of error
                apply_sql_script(conn, fullname)
                self._insert_script(script, conn)
        if scripts:  # save the last version
            self.version = scripts[-1]['version']

    def from_scratch(self, conn):
        self._from_to_version(conn, None, None, ())

    def get_db_version(self, conn):
        """
        Get the latest version of the database by looking at the
        version table.
        """
        curs = conn.cursor()
        try:
            curs.execute(
                'select max(version) from {}'.format(self.version_table))
            return curs.fetchall()[0][0]
        except:
            raise VersioningNotInstalled('Run openquake --upgrade-db')

    def check_version(self, conn):
        scripts = self.read_scripts(db_versions=self.get_db_versions(conn))
        if scripts:
            raise SystemExit(
                'Your database is not updated. You can update it by running '
                'openquake --upgrade-db which will process the '
                'following new versions: %s' % [s['version'] for s in scripts])

    def get_db_versions(self, conn):
        """
        Get all the versions stored in the database as a set
        """
        curs = conn.cursor()
        query = 'select version from {}'.format(self.version_table)
        try:
            curs.execute(query)
            return set(version for version, in curs.fetchall())
        except:
            raise VersioningNotInstalled(
                'perform the steps in the documentation')

    def get_max_version(self):
        '''
        Get the maximum version from the upgrade scripts. Return None
        if there are no scripts.
        '''
        version = None
        for scriptname in sorted(os.listdir(self.upgrade_dir)):
            match = self.parse_script_name(scriptname)
            if match:
                version = match['version']
        return version

    def parse_script_name(self, fname):
        '''
        Parse a script name and return a dictionary with fields
        fname, name, version and ext (or None if the name does not match).
        '''
        match = re.match(self.pattern, fname)
        if not match:
            return
        version, name, ext = match.groups()
        return dict(fname=fname, version=version, name=name, ext=ext)

    def read_scripts(self, minversion=None, maxversion=None, db_versions=()):
        """
        Extract the upgrade scripts from a directory as a list of
        dictionaries, ordered by version.
        """
        scripts = []
        versions = {}  # a script is unique per version
        for scriptname in sorted(os.listdir(self.upgrade_dir)):
            match = self.parse_script_name(scriptname)
            if match:
                version = match['version']
                if version in db_versions:
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


def upgrade_db(conn, pkg_name):
    """
    Upgrade a database by running several scripts in a single transaction.

    :param conn: a DB API 2 connection
    :pkg_name: the name of the package containing the upgrade scripts
    """
    curs = conn.cursor()
    try:
        # upgrader is an UpgradeManager instance defined in the __init__.py
        upgrader = importlib.import_module(pkg_name).upgrader
    except ImportError:
        raise SystemExit(
            'Could not import %s (not in the PYTHONPATH?)' % pkg_name)
    if not upgrader.read_scripts():
        raise SystemExit('The upgrade_dir does not contain scripts matching '
                         'the pattern %s' % upgrader.pattern)
    curs.execute("SELECT tablename FROM pg_tables WHERE tablename=%s",
                 (upgrader.version_table,))
    versioning_table = curs.fetchall()
    if not versioning_table:
        upgrader.install_versioning(conn)
    try:
        upgrader.upgrade(conn)
    except:
        conn.rollback()
        raise
    else:
        conn.commit()
