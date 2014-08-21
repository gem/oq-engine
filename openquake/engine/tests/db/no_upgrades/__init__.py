import os
from openquake.engine.db.upgrade_manager import UpgradeManager

directory = os.path.abspath(os.path.dirname(__file__))
upgrader = UpgradeManager(directory, version_table='test.version')
