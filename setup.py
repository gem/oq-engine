from setuptools import setup, find_packages


README="""
OpenQuake is an open source application that allows users to
compute seismic hazard and seismic risk of earthquakes on a global scale.

Please note: the /usr/bin/openquake script requires a celeryconfig.py
file in the PYTHONPATH.  Please make sure this is the case and that your
celeryconfig.py file works with your python-celery setup.

Feel free to copy /usr/openquake/celeryconfig.py and revise it as needed.
"""


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
    version = "0.8.3",
    author = "The OpenQuake team",
    author_email = "info@openquake.org",
    description = ("Computes hazard, risk and socio-economic impact of "
                   "earthquakes."),
    license = "AGPL3",
    keywords = "earthquake seismic hazard risk",
    url = "http://openquake.org/",
    long_description=README,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
    ],
   packages = find_packages(exclude=['bin', 'bin.*', 'qa_tests', 'qa_tests.*', 'tools', "tests", "tests.*", "openquake.bin.oqpath", "openquake.bin.oqpath.*", "openquake.nrml.tests", "openquake.nrml.tests.*" ]),
   include_package_data=True,
   package_data={'openquake': ['db/schema/*',
                               'nrml/schema/hazard/*', 'nrml/schema/risk/*', 'nrml/schema/gml/*',
                               'nrml/schema/GML-SimpleFeaturesProfileSchema.xsd',
                               'nrml/schema/nrml_common.xsd', 'nrml/schema/nrml.xsd',
                               'nrml/schema/xlinks/*', 'logging.cfg', 'openquake.cfg', 'README', 'LICENSE' ]},
   exclude_package_data = { '': ['openquake/bin/oqpath.py'] },
    scripts = [
        "openquake/bin/oq_create_db", "openquake/bin/oq_restart_workers"]
)
