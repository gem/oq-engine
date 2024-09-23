(slurm)=

# Running on a SLURM cluster (experimental)

Most HPC clusters support a scheduler called SLURM (
Simple Linux Utility for Resource Management). The OpenQuake engine
is able to transparently interface with SLURM.

## Running OpenQuake calculations with SLURM

Let's consider a user with ssh access to a SLURM cluster. The only
thing the user has to do after logging in is to load the openquake
libraries with the command
```
$ load module openquake
```
Then running a calculation is quite trivial. The user has two choices:
to run the calculation on a single node with the command
```
$ oq engine --run job.ini
```
or running the calculation on multiple nodes with a command like
```
$ oq engine --run job.ini --nodes=4
```
which will split the calculation over 4 nodes. Clearly, there are
limitations on the number of available nodes, so if you set a number
of nodes which is too large you can have one of the following:

1. an error "You can use at most N nodes"; N depends on the
   configuration chosen your system administrator and can be inferred from
   the parameters in the openquake.cfg file as `max_cores / num_cores`;
   for instance for `max_cores=1024` and `num_cores=128` you would have `N=8`

2. a non-starting calculation, forever waiting for resources that
   cannot be allocated; you can see if you are in this situation
   by giving the command `$ squeue -u $USER` and looking at the reason
   why the nodelist is not being allocated (check for `AssocMaxCpuPerJobLimit`)

3. a non-starting calculation, waiting for resources which *can* be allocated,
   it is just a matter of waiting; in this case the reason will be
   `Resources` (waiting for resources to become available) or `Priority`
   (queued behind a higher priority job).

If you are stuck in situation 2 you must kill the openquake job and the
SLURM job with the command `scancel JOBID` (JOBID is listed by the
command `$ squeue -u $USER`). If you are stuck in situation 3 for a long
time it can be better to kill the jobs (both openquake and SLURM) and
then relaunch the calculations, this time asking for fewer nodes.

## Running out of quota

The engine will store the calculation files in `shared_dir`
and some auxiliary files in `custom_dir`; both directories are
mandatory and must be specified in the configuration file. The
`shared_dir` is meant to point to the work area of the cluster
and the `custom_tmp` to the scratch area of the cluster.

Classical calculations will generate an .hdf5 file for each
task spawned, so each calculation can spawn thousands of files.
We suggest to periodically purge the scratch directories for
old calculations, which will have the form `scratch_dir/calc_XXX`.

## Installing on HPC

This section is for the administrators of the HPC cluster.

Here are the installations instructions to create modules for
engine 3.18 assuming you have python3.10 installed as modules.

We recommend choosing a base path for openquake and then installing 
the different versions using the release number, in our example /apps/openquake/3.18.
This will create different modules for different releases

```
# module load python/3.10
# mkdir /apps/openquake
# python3.10 -m venv /apps/openquake/3.18
# source /apps/openquake/3.18/bin/activate
# pip install -U pip
# pip install -r https://github.com/gem/oq-engine/raw/engine-3.18/requirements-py310-linux64.txt
# pip install openquake.engine==3.18
```
Then you have to define the module file. In our cluster it is located in
`/apps/Modules/modulefiles/openquake/3.18`, please use the appropriate
location for your cluster. The content of the file should be the following:
```
#%Module1.0
##
proc ModulesHelp { } {

  puts stderr "\tOpenQuake - loads the OpenQuake environment"
  puts stderr "\n\tThis will add OpenQuake to your PATH environment variable."
}

module-whatis   "loads the OpenQuake 3.18 environment"

set     version         3.18
set     root    /apps/openquake/3.18 

prepend-path    LD_LIBRARY_PATH $root/lib64
prepend-path    MANPATH         $root/share/man
prepend-path    PATH            $root/bin
prepend-path    PKG_CONFIG_PATH $root/lib64/pkgconfig
prepend-path    XDG_DATA_DIRS   $root/share
```
After installing the engine, the sysadmin has to edit the file
`/opt/openquake/venv/openquake.cfg` and set a few parameters:
```
[distribution]
oq_distribute = slurm
serialize_jobs = 2
python = /apps/openquake/3.18/bin/python

[directory]
# optionally set it to something like /mnt/large_shared_disk
shared_dir =

[dbserver]
host = local
```
With `serialize_jobs = 2` at most two jobs per user can run concurrently. You may want to
increase or reduce this number. Each user will have its own database located in
`$HOME/oqdata/db.sqlite3`. The database will be created automatically
the first time the user runs a calculation (NB: in engine-3.18 it must be
created manually with the command `srun oq engine --upgrade-db --yes`).

## How it works internally

The support for SLURM is implemented in the module
`openquake/baselib/parallel.py`. The idea is to submit to SLURM a job
array of tasks for each parallel phase of the calculation. For instance
a classical calculations has three phases: preclassical, classical
and postclassical.

The calculation will start sequentially, then it will reach the
preclassical phase: at that moment the engine will create a
bash script called `slurm.sh` and located in the directory
`$HOME/oqdata/calc_XXX` being XXX the calculation ID, which is
an OpenQuake concept and has nothing to do with the SLURM ID.
The `slurm.sh` script has the following template:
```bash
#!/bin/bash
#SBATCH --job-name={mon.operation}
#SBATCH --array=1-{mon.task_no}
#SBATCH --time=10:00:00
#SBATCH --mem-per-cpu=1G
#SBATCH --output={mon.calc_dir}/%a.out
#SBATCH --error={mon.calc_dir}/%a.err
srun {python} -m openquake.baselib.slurm {mon.calc_dir} $SLURM_ARRAY_TASK_ID
```
At runtime the `mon.` variables will be replaced with their values:

- `mon.operation` will be the string "preclassical"
- `mon.task_no` will be the total number of tasks to spawn
- `mon.calc_dir` will be the directory `$HOME/oqdata/calc_XXX`
- `python` will be the path to the python executable to use, as set in openquake.cfg

System administrators may want to adapt such template. At the moment
this requires modifying the engine codebase; in the future the template
may be moved in the configuration section.

A task in the OpenQuake engine is simply a Python function or
generator taking some arguments and a monitor object (`mon`),
sending results to the submitter process via zmq.

Internally the engine will save the input arguments for each task
in pickle files located in `$HOME/oqdata/calc_XXX/YYY.pik`, where
XXX is the calculation ID and YYY is the `$SLURM_ARRAY_TASK_ID` starting from 1
to the total number of tasks.

The command `srun {python} -m openquake.baselib.slurm {mon.calc_dir}
$SLURM_ARRAY_TASK_ID` in `slurm.sh` will submit the tasks in parallel
by reading the arguments from the input files.

Using a job array has the advantage that all tasks can be killed
with a single command. This is done automatically by the engine
if the user aborts the calculation or if the calculation fails
due to an error.
