import re
import sys
from setuptools import setup, find_packages


def get_version():
    version_re = r"^__version__\s+=\s+['\"]([^'\"]*)['\"]"
    version = None

    package_init = 'openquake/engine/__init__.py'
    for line in open(package_init, 'r'):
        version_match = re.search(version_re, line, re.M)
        if version_match:
            version = version_match.group(1)
            break
    else:
        sys.exit('__version__ variable not found in %s' % package_init)

    return version

version = get_version()

url = "http://openquake.org/"

README = """
OpenQuake is an open source application that allows users to
compute seismic hazard and seismic risk of earthquakes on a global scale.

Please note: the /usr/bin/openquake script requires a celeryconfig.py
file in the PYTHONPATH.  Please make sure this is the case and that your
celeryconfig.py file works with your python-celery setup.

Feel free to copy /usr/openquake/engine/celeryconfig.py and revise it
as needed.
"""

PY_MODULES = ['openquake.engine.bin.openquake_cli']

setup(
    entry_points={
        "console_scripts": [
            "oq-engine = openquake.engine.bin.openquake_cli:main"
        ]
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
                                    "tools",
                                    "openquake.engine.bin",
                                    "openquake.engine.bin.*"]),
    py_modules=PY_MODULES,

    include_package_data=True,
    package_data={"openquake.engine": [
        "db/schema/upgrades/*.sql",
        "openquake.cfg", "openquake_worker.cfg", "README", "LICENSE"]},
    scripts=["openquake/engine/bin/oq_create_db",
             "openquake/engine/bin/openquake"],

    namespace_packages=['openquake'],

    zip_safe=False,
    )
