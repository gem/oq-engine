import os
import pytest

import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

def test_hosts_file(host):
    """Validate /opt/openquake/bin/oq file."""
    f = host.file("/opt/openquake/bin/oq")

    assert f.exists
    assert f.user == "root"
    assert f.group == "root"
