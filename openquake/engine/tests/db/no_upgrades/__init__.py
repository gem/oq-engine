import os
from openquake.engine.db.upgrade_manager import UpgradeManager

version_pattern = r'\d\d'
version_table = 'test.version'
directory = os.path.abspath(os.path.dirname(__file__))
upgrader = UpgradeManager(version_pattern, directory, version_table)
