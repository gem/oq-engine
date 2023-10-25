Introduction
============

The goal of this manual is to provide a comprehensive and transparent
description of the features of the OpenQuake Engine. This manual is
designed to be readable by someone with basic understanding of
Probabilistic Seismic Hazard and Risk Analysis, but no previous
knowledge of the OpenQuake engine is assumed.

The OpenQuake engine is an effort promoted and actively developed by the GEM Foundation,
a public-private partnership initiated by the Global Science Forum of
the Organisation for Economic Co-operation and Development (OECD) [1]_.

The OpenQuake engine is the result of an effort carried out jointly by the
Information Technology and Scientific teams working at the GEM Foundation
Secretariat. It is freely distributed under an Affero GPL license
(http://www.gnu.org/licenses/agpl-3.0.html).


.. _`chap:intro`:

OpenQuake-engine Background
---------------------------

Overview
^^^^^^^^

OpenQuake-engine is the seismic hazard and risk calculation software
developed by the GEM Foundation. By following current standards in software
developments like test-driven development and continuous integration,
the OpenQuake engine aims at becoming an open, and community-driven tool for
seismic hazard and risk analysis.

The source code of the OpenQuake engine is available on a public web-based
repository at the following address: http://github.com/gem/oq-engine.

The OpenQuake engine is available for the Linux, macOS, and Windows platforms. It
can be installed in several different ways. The following page provides
a handy guide for users to choose the most appropriate installation
method depending on their intended use cases:

https://github.com/gem/oq-engine/blob/engine-3.18/doc/installing/README.md.

This user manual is for the command line interface for the OpenQuake engine.

Supplementary resources
^^^^^^^^^^^^^^^^^^^^^^^

Guidance instructions for using the OpenQuake engine WebUI are available at
https://github.com/gem/oq-engine/blob/engine-3.18/doc/running/server.md.

A user manual for the QGIS plugin for the OpenQuake engine is available at
https://docs.openquake.org/oq-irmt-qgis/latest/. In particular,
instructions for using the plugin as an interface for running OpenQuake engine
calculations are listed in Chapter 14, and methods for using the plugin
for visualization of hazard and risk outputs are listed in Chapter 15.

A manual intended for more advanced users of the OpenQuake engine is available at
https://docs.openquake.org/oq-engine/advanced/OpenQuakeforAdvancedUsers.pdf.

Interested users are also encouraged to peruse the `OpenQuake Hazard
Science <https://storage.globalquakemodel.org/media/cms_page_media/432/oqhbt_BkpnqP8.pdf>`__
and `OpenQuake Risk
Science <https://storage.globalquakemodel.org/media/cms_page_media/432/oq-risk-manual-1_0.pdf>`__
books, which provide explanations of the scientific methodologies
adopted in the implementation of the earthquake hazard and risk
libraries of the OpenQuake engine.

Subscribe to the OpenQuake users mailing list to keep abreast of the
latest announcements from the OpenQuake development team, to ask and
answer questions related to the OpenQuake engine and participate in the ongoing
discussions: https://groups.google.com/g/openquake-users

Launching a calculation
^^^^^^^^^^^^^^^^^^^^^^^

An OpenQuake engine analysis is launched from the command line of a terminal.

A schematic list of the options that can be used for the execution of
the OpenQuake engine can be obtained with the following command:

.. code:: shell-session

   user@ubuntu:~$ oq engine --help

The result is the following:

.. code:: shell-session

   usage: oq engine [-h] [--log-file LOG_FILE] [--no-distribute] [-y]
                    [-c CONFIG_FILE] [--make-html-report YYYY-MM-DD|today] [-u]
                    [-d] [-w] [--run JOB_INI [JOB_INI ...]]
                    [--list-hazard-calculations] [--list-risk-calculations]
                    [--delete-calculation CALCULATION_ID]
                    [--delete-uncompleted-calculations]
                    [--hazard-calculation-id HAZARD_CALCULATION_ID]
                    [--list-outputs CALCULATION_ID] [--show-log CALCULATION_ID]
                    [--export-output OUTPUT_ID TARGET_DIR]
                    [--export-outputs CALCULATION_ID TARGET_DIR] [-e]
                    [-l {debug, info, warn, error, critical}] [-r]
                    [--param PARAM]

   Run a calculation using the traditional command line API

   optional arguments:
     -h, --help            show this help message and exit
     --log-file LOG_FILE, -L LOG_FILE
                           Location where to store log messages; if not
                           specified, log messages will be printed to the console
                           (to stderr)
     --no-distribute, --nd
                           Disable calculation task distribution and run the
                           computation in a single process. This is intended for
                           use in debugging and profiling.
     -y, --yes             Automatically answer "yes" when asked to confirm an
                           action
     -c CONFIG_FILE, --config-file CONFIG_FILE
                           Custom openquake.cfg file, to override default
                           configurations
     --make-html-report YYYY-MM-DD|today, --r YYYY-MM-DD|today
                           Build an HTML report of the computation at the given
                           date
     -u, --upgrade-db      Upgrade the openquake database
     -d, --db-version      Show the current version of the openquake database
     -w, --what-if-I-upgrade
                           Show what will happen to the openquake database if you
                           upgrade
     --run JOB_INI [JOB_INI ...]
                           Run a job with the specified config file
     --list-hazard-calculations, --lhc
                           List hazard calculation information
     --list-risk-calculations, --lrc
                           List risk calculation information
     --delete-calculation CALCULATION_ID, --dc CALCULATION_ID
                           Delete a calculation and all associated outputs
     --delete-uncompleted-calculations, --duc
                           Delete all the uncompleted calculations
     --hazard-calculation-id HAZARD_CALCULATION_ID, --hc HAZARD_CALCULATION_ID
                           Use the given job as input for the next job
     --list-outputs CALCULATION_ID, --lo CALCULATION_ID
                           List outputs for the specified calculation
     --show-log CALCULATION_ID, --sl CALCULATION_ID
                           Show the log of the specified calculation
     --export-output OUTPUT_ID TARGET_DIR, --eo OUTPUT_ID TARGET_DIR
                           Export the desired output to the specified directory
     --export-outputs CALCULATION_ID TARGET_DIR, --eos CALCULATION_ID TARGET_DIR
                           Export all of the calculation outputs to the specified
                           directory
     -e, --exports         Comma-separated string specifing the export formats,
                           in order of priority
     -l, --log-level {debug, info, warn, error, critical}
                           Defaults to "info"
     -r, --reuse-input    Read the sources|exposures from the cache (if any)
     --param PARAM, -p PARAM
                           Override parameters specified with the syntax
                           NAME1=VALUE1,NAME2=VALUE2,...

.. [1]
   | A short description of the process promoted by OECD is available
     here:
   | `http://www.oecd.org/science/sci-tech/theglobalearthquakemodelgem.htm <https://web.archive.org/web/20170714033553/https://www.oecd.org/science/sci-tech/theglobalearthquakemodelgem.htm>`__


