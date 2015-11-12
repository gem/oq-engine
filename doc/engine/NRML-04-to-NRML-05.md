Migration from NRML 0.4 to NRML 0.5
-----------------------------------

In OpenQuake 1.6 the format of the risk model files (previously known as
NRML 0.4) has been changed. The new format is incompatible with the previous
one, however you should not worry because

1. the old format is still recognized by the engine
2. there is a conversion script to migrate from NRML 0.4 to NRML 0.5

You are not forced to migrate, since the old format is still
supported, however the migration will get rid of the annoying
deprecation warnings that you will see everytime you run a calculation
with files using the NRML 0.4 format.

The command to migrate recursively all the risk models inside a directory
and its subdirectories is the following:

$ oq-lite upgrade_nrml <directory>

The files will be replaced with files in the NRML 0.5 format; the old files will
not be deleted, just renamed by appending a `.bak` extension to them.

When running a calculation, you may get an error like this:

ValueError: Error in the file "structural_vulnerability_file=/home/.../vulnerability_model.xml": lossCategory is of type "economic_loss", expected "structural"

The reason is that in NRML 0.4 the `lossCategory` attribute had no
special meaning (actually it was ignored by the engine) whereas now
there is a check on it. It must be consistent with the name of the
variable used in the configuration file. In this example in the
job_risk.ini file there was a line `structural_vulnerability_file=`,
so the `lossCategory` is expected to be of kind `structural`. Edit the
"vulnerability_model.xml" file and set the `lossCategory` attribute to
the expected value. 

Valid loss categories are `structural`, `nonstructural`, `contents`,
`business_interruption` and `fatalities`.  There is now a strict check
on the categories, both in the risk model files and in the exposure
file.
