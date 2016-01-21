import os
from openquake.server.db.upgrade_manager import UpgradeManager

upgrader = UpgradeManager(os.path.abspath(os.path.dirname(__file__)))
