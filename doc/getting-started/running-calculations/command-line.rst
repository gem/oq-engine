Using the Command Line
======================

An OpenQuake engine analysis can be launched from the command line of a terminal.

A schematic list of the options that can be used for the execution of the OpenQuake engine can be obtained with the 
following command::

	user@ubuntu:~$ oq engine --help

The result is the following::

	usage: oq engine [-h] [--no-distribute] [-y] [-u] [-d] [-w]
	                 [--list-hazard-calculations] [--list-risk-calculations]
	                 [--delete-uncompleted-calculations] [-m] [-L LOG_FILE]
	                 [--make-report YYYY-MM-DD|today]
	                 [--run JOB_INI [JOB_INI ...]]
	                 [--delete-calculation CALCULATION_ID]
	                 [--hazard-calculation-id HAZARD_CALCULATION_ID]
	                 [--list-outputs CALCULATION_ID] [--show-log CALCULATION_ID]
	                 [--export-output OUTPUT_ID TARGET_DIR]
	                 [--export-outputs CALCULATION_ID TARGET_DIR] [-p [PARAM ...]]
	                 [-e ] [-l {debug, info, warn, error, critical}]
	                 [--sample-sources False] [-n 1]

	Run a calculation using the traditional command line API

	options:
	  -h, --help            show this help message and exit
	  --no-distribute, --nd
	                        Disable calculation task distribution and run the
	                        computation in a single process. This is intended for
	                        use in debugging and profiling.
	  -y, --yes             Automatically answer "yes" when asked to confirm an
	                        action
	  -u, --upgrade-db      Upgrade the openquake database
	  -d, --db-version      Show the current version of the openquake database
	  -w, --what-if-I-upgrade
	                        Show what will happen to the openquake database if you
	                        upgrade
	  --list-calculations, --lc
	                        List all calculations information
	  --list-hazard-calculations, --lhc
	                        List hazard calculations information
	  --list-risk-calculations, --lrc
	                        List risk calculations information
	  --delete-uncompleted-calculations, --duc
	                        Delete all the uncompleted calculations
	  -m, --multi           Run multiple job.inis (usually scenarios) in parallel
	  -L, --log-file LOG_FILE
	                        Location where to store log messages; if not
	                        specified, log messages will be printed to the console
	                        (to stderr)
	  --make-report, --r YYYY-MM-DD|today
	                        Build an HTML report of the computation at the given
	                        date
	  --run, --run JOB_INI [JOB_INI ...]
	                        Run a job with the specified config file
	  --delete-calculation, --dc CALCULATION_ID
	                        Delete a calculation and all associated outputs
	  --hazard-calculation-id, --hc HAZARD_CALCULATION_ID
	                        Use the given job as input for the next job
	  --list-outputs, --lo CALCULATION_ID
	                        List outputs for the specified calculation
	  --show-log, --sl CALCULATION_ID
	                        Show the log of the specified calculation
	  --export-output, --eo OUTPUT_ID TARGET_DIR
	                        Export the desired output to the specified directory
	  --export-outputs, --eos CALCULATION_ID TARGET_DIR
	                        Export all of the calculation outputs to the specified
	                        directory
	  -p, --param [PARAM ...]
	                        Override parameters specified with the syntax
	                        NAME1=VALUE1 NAME2=VALUE2 ...
	  -e, --exports         Comma-separated string specifing the export formats,
	                        in order of priority
	  -l, --log-level {debug, info, warn, error, critical}
	                        Defaults to "info"
	  --sample-sources, --ss False
	                        Sample fraction in the range 0..1
	  -n, --nodes 1         Number of SLURM nodes (if applicable)
