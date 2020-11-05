"""Role testing files using testinfra."""


def test_hosts_file(host):
    """Validate /opt/openquake/bin/oq file."""
    f = host.file("/opt/openquake/bin/oq")

    assert f.exists
    assert f.user == "root"
    assert f.group == "root"
