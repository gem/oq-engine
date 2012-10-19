import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    entry_points = {
        'console_scripts': [
            'openquake = openquake.bin.oqscript:main',
            'oq_cache_gc = openquake.bin.cache_gc:main',
            'oq_monitor = openquake.bin.openquake_supervisor:main',
            'oq_check_monitors = openquake.supervising.supersupervisor:main',
            'oq_log_sink = openquake.bin.openquake_messages_collector:main',
            ]},
    name = "openquake",
    version = "0.8.2",
    author = "The OpenQuake team",
    author_email = "info@openquake.org",
    description = ("Computes hazard, risk and socio-economic impact of "
                   "earthquakes."),
    license = "AGPL3",
    keywords = "earthquake seismic hazard risk",
    url = "http://openquake.org/",
    long_description=read('openquake/README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
    ],
    packages = find_packages(),
    include_package_data=True,
    scripts = [
        "openquake/bin/oq_create_db", "openquake/bin/oq_restart_workers"]
)
