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
        the name of the table containing the versions [ex. public.db_version]
    """
    def __init__(self, version_pattern, upgrade_dir,
                 version_table='public.db_version'):
        self.upgrade_dir = upgrade_dir
        self.version_pattern = version_pattern
        self.pattern = r'^(%s[rs]?)-([\w\-_]+)\.(sql|py)$' % version_pattern
        self.version_table = version_table
        if '.' in version_table:  # contains the schema name
            self.version_schema_name, self.version_table_name = \
                version_table.split('.')
        else:  # assume the schema name is 'public'
            self.version_schema_name, self.version_table_name = \
                ('public', self.version_table)
        if re.match('[\w_\.]+', version_table) is None:
            raise ValueError(version_table)
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
        logs.LOG.info('Creating the versioning table %s', self.version_table)
        conn.cursor().execute(CREATE_VERSIONING % self.version_table)
        self._insert_script(self.read_scripts()[0], conn)

    def init(self, conn):
        """
        Create the version table and run the base script on an empty database.

        :param conn: a DB API 2 connection
        """
        base = self.read_scripts()[0]['fname']
        logs.LOG.info('Creating the initial schema from %s',  base)
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
        if not scripts:
            logs.LOG.warn('The database is updated at version %s. '
                          'Nothing to do.', self.starting_version)
            return []
        self.ending_version = max(s['version'] for s in scripts)
        logs.LOG.warn('The database is at version %s. Upgrading to version '
                      '%s.', self.starting_version, self.ending_version)
        return self._upgrade(conn, scripts)

    def _upgrade(self, conn, scripts):
        versions_applied = []
        for script in scripts:  # script is a dictionary
            fullname = os.path.join(self.upgrade_dir, script['fname'])
            logs.LOG.info('Executing %s', fullname)
            if script['ext'] == 'py':  # Python script with a upgrade(conn)
                runpy.run_path(fullname)['upgrade'](conn)
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
        :returns: a list with the versions that will be applied
        """
        scripts = self.read_scripts(skip_versions=self.get_db_versions(conn))
        versions = [s['version'] for s in scripts]
        if scripts:
            raise SystemExit(
                'Your database is not updated. You can update it by running '
                'openquake --upgrade-db which will process the '
                'following new versions: %s' % versions)
        return versions

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
        except:
            raise VersioningNotInstalled('Run openquake --upgrade-db')

    def parse_script_name(self, script_name):
        '''
        Parse a script name and return a dictionary with fields
        fname, name, version and ext (or None if the name does not match).

        :param name: name of the script
        '''
        match = re.match(self.pattern, script_name)
        if not match:
            return
        version, name, ext = match.groups()
        return dict(fname=script_name, version=version, name=name, ext=ext)

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


def upgrade_db(conn, pkg_name, from_scratch=False, skip_versions=()):
    """
    Upgrade a database by running several scripts in a single transaction.

    :param conn: a DB API 2 connection
    :param str pkg_name: the name of the package containing the upgrade scripts
    :param bool from_scratch: whether to run the base creation script
    :param list skip_versions: the versions to skip
    :returns: the version numbers of the new scripts applied the database
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
    try:
        if from_scratch:  # assume an empty db
            # run the base schema script
            upgrader.init(conn)
        else:  # already populated db
            # check if there is already a versioning table
            curs.execute("SELECT tablename FROM pg_tables "
                         "WHERE schemaname=%s AND tablename=%s",
                         (upgrader.version_schema_name,
                          upgrader.version_table_name))
            versioning_table = curs.fetchall()
            # if not, create it
            if not versioning_table:
                upgrader.install_versioning(conn)
        # run the upgrade scripts
        versions_applied = upgrader.upgrade(conn, skip_versions)
    except:
        conn.rollback()
        raise
    else:
        conn.commit()

    return versions_applied
