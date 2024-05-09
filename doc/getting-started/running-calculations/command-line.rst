Running the OpenQuake engine through the Command Line
=====================================================

An OpenQuake engine analysis can be launched from the command line of a terminal.

A schematic list of the options that can be used for the execution of the OpenQuake engine can be obtained with the 
following command::

	user@ubuntu:~$ oq engine --help

The result is the following::

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