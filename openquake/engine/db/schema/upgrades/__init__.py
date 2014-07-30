import os
from sqlplain import upgrade_manager

version_pattern = r'\d\d\d\d'
version_table = 'revision_info'
directory = os.path.abspath(os.path.dirname(__file__))

upgrade = upgrade_manager.UpgradeManager(
    version_pattern, directory, version_table, echo=True)
