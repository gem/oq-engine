from setuptools import setup, find_packages

version = "1.0.0"
url = "http://openquake.org/"

README = """
OpenQuake is an open source application that allows users to
compute seismic hazard and seismic risk of earthquakes on a global scale.

Please note: the /usr/bin/openquake script requires a celeryconfig.py
file in the PYTHONPATH.  Please make sure this is the case and that your
celeryconfig.py file works with your python-celery setup.

Feel free to copy /usr/openquake/engine/celeryconfig.py and revise it as needed.
"""

PY_MODULES = ['openquake.engine.bin.cache_gc', 'openquake.engine.bin.oqscript']

setup(
    entry_points={
        "console_scripts": ["openquake = openquake.engine.bin.oqscript:main"]
    },
    name="openquake.engine",
    version=version,
    author="The OpenQuake team",
    author_email="devops@openquake.org",
    description=("Computes hazard, risk and socio-economic impact of "
                 "earthquakes."),
    license="AGPL3",
    keywords="earthquake seismic hazard risk",
    url=url,
    long_description=README,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
    ],
    packages=find_packages(exclude=["qa_tests", "qa_tests.*",
                                    "tools", "tests", "tests.*",
                                    "openquake.engine.bin",
                                    "openquake.engine.bin.*"]),
    py_modules=PY_MODULES,

    include_package_data=True,
    package_data={"openquake.engine": [
        "db/schema/*.sql", "db/schema/upgrades/*/*/*.sql",
        "openquake.cfg", "README", "LICENSE"]},
    exclude_package_data={"": ["bin/oqpath.py", "bin/oq_check_monitors",
                               "bin/oq_log_sink"]},
    scripts=["openquake/engine/bin/oq_create_db"],

    namespace_packages=['openquake'],

    zip_safe=False,
    )
