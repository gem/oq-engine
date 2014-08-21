import os
from openquake.engine.db.upgrade_manager import UpgradeManager

upgrader = UpgradeManager(os.path.abspath(os.path.dirname(__file__)))
