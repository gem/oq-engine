from setuptools import setup, find_packages

version = "1.2.0"
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
    scripts=["openquake/engine/bin/oq_create_db"],

    namespace_packages=['openquake'],

    zip_safe=False,
    )
