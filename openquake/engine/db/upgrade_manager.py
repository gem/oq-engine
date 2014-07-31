import os
import re
import sys
import runpy
from openquake.engine.db import util


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


# errors are not trapped on purpose, sincetransactions should be managed
# in client code
class UpgradeManager(object):

    def __init__(self, version_pattern, upgrade_dir,
                 version_table='sqlplain_versioning', echo=False):
        self.upgrade_dir = upgrade_dir
        self.version_pattern = version_pattern
        self.pattern = r'^(%s[rs]?)-([\w\-_]+)\.(sql|py)$' % version_pattern
        self.version_table = version_table
        if re.match('[\w_\.]+', version_table) is None:
            raise ValueError(version_table)
        self.echo = echo
        self.version = None  # will be updated after the run
        self.starting_version = None  # will be updated after the run

    def _insert_script(self, script, conn):
        conn.execute(
            'INSERT INTO {} VALUES (%s, %s)'.format(self.version_table),
            (script['version'], script['name']))

    def install_versioning(self, conn):
        """
        Create the version table into an already populated database
        and insert the base script.
        """
        conn.execute(CREATE_VERSIONING % self.version_table)
        self._insert_script(self.read_scripts()[0], conn)

    def init_db(self, conn):
        """
        Create the version table and run the base script on an empty database.
        """
        base = self.read_scripts()[0]['fname']
        util.create_from_filename(os.path.join(self.upgrade_dir, base))(conn)
        self.install_versioning(conn)

    def _from_to_version(self, conn, from_version, to_version, db_versions):
        scripts = self.read_scripts(from_version, to_version, db_versions)
        for script in scripts:  # script is a dictionary
            fullname = os.path.join(self.upgrade_dir, script['fname'])
            if self.echo:
                sys.stderr.write('Executing %s\n' % fullname)
            if script['ext'] == 'py':  # Python script with a upgrade(conn)
                runpy.run_path(fullname)['upgrade'](conn)
                self._insert_script(script, conn)
            else:  # SQL script
                # notice that this prints the file name in case of error
                util.create_from_filename(fullname)(conn)
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
        try:
            return conn.scalar(
                'select max(version) from {}'.format(self.version_table))
        except:
            raise VersioningNotInstalled(
                '%(database)s: perform the steps in the documentation'
                % conn.uridict)

    def check_version(self, conn):
        scripts = self.read_scripts(db_versions=self.get_db_versions(conn))
        if scripts:
            raise SystemExit(
                'Your database is not updated. You can update it by running '
                'bin/oq_upgrade which will process the following new versions:'
                ': %s' % [s['version'] for s in scripts])

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
                '%(database)s: perform the steps in the documentation'
                % conn.uridict)

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

    def upgrade(self, conn):
        '''
        Upgrade the database from the current version to the maximum
        version in the upgrade scripts.
        '''
        db_versions = self.get_db_versions(conn)
        self.starting_version = sorted(db_versions)[-1]  # the highest version
        self.ending_version = self.get_max_version()
        if self.starting_version == self.ending_version:
            print 'The database is updated at version %s. Nothing to do.' % (
                self.starting_version)
            return
        print 'The database is at version %s. Upgrading to version %s.' % (
            self.starting_version, self.ending_version)
        self._from_to_version(conn, self.starting_version, self.ending_version,
                              db_versions=db_versions)

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
