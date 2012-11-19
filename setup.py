from setuptools import setup, find_packages, findall


README = """
OpenQuake is an open source application that allows users to
compute seismic hazard and seismic risk of earthquakes on a global scale.

Please note: the /usr/bin/openquake script requires a celeryconfig.py
file in the PYTHONPATH.  Please make sure this is the case and that your
celeryconfig.py file works with your python-celery setup.

Feel free to copy /usr/openquake/celeryconfig.py and revise it as needed.
"""

py_not_modules=["openquake/bin/__init__.py", "openquake/bin/oqpath.py",
                "openquake/bin/openquake_messages_collector.py"]
py_modules=[f for f in findall('openquake/bin') if f not in py_not_modules ]
print "pippo"
print py_modules
for i, el in enumerate(py_modules):
    py_modules[i] = el.replace("/", ".")

for i, el in enumerate(py_modules):
    if el.endswith('.py'):
       py_modules[i] = el[:-3]

setup(
    entry_points={
        "console_scripts": [
            "noq = openquake.bin.oqscript:main",
            "oq_cache_gc = openquake.bin.cache_gc:main",
            "oq_monitor = openquake.bin.openquake_supervisor:main",
            ]},
    name="noq",
    version="0.2",
    author="The OpenQuake team",
    author_email="info@openquake.org",
    description=("Computes hazard, risk and socio-economic impact of "
                 "earthquakes."),
    license="AGPL3",
    keywords="earthquake seismic hazard risk",
    url="http://openquake.org/",
    long_description=README,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        ],
    packages=find_packages(exclude=["qa_tests", "qa_tests.*",
                                    "tools", "tests", "tests.*",
                                    "openquake.bin",
                                    "openquake.bin.*",
                                    "openquake.nrml.tests",
                                    "openquake.nrml.tests.*"]),
    py_modules=py_modules,

    include_package_data=True,
    package_data={"openquake": [
            "db/schema/*",
            "nrml/schema/hazard/*", "nrml/schema/risk/*", "nrml/schema/gml/*",
            "nrml/schema/GML-SimpleFeaturesProfileSchema.xsd",
            "nrml/schema/nrml_common.xsd", "nrml/schema/nrml.xsd",
            "nrml/schema/xlinks/*", "logging.cfg", "openquake.cfg",
            "README", "LICENSE"]},
    exclude_package_data={"": ["bin/oqpath.py", "bin/oq_check_monitors", "bin/oq_log_sink"]},
    scripts=[
        "openquake/bin/oq_create_db", "openquake/bin/oq_restart_workers" ]
    )
