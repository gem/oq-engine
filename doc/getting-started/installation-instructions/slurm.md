(slurm)=

# Running the OpenQuake Engine on a SLURM cluster

Most HPC clusters support a scheduler called SLURM (
Simple Linux Utility for Resource Management). The OpenQuake engine
is able to interface with SLURM to make use of all the resources
of the cluster.

## Running OpenQuake calculations with SLURM

Let's consider a user with ssh access to a SLURM cluster. The only
thing she has to do after logging in is to load the openquake
libraries with the command
```
$ load module openquake
```
Then running a calculation is quite trivial. The user has two choices:
running the calculation on-the-fly with the command
```
$ srun oq engine --run job.ini
```
or running the calculation in a batch with the command
```
$ sbatch oq engine --run job.ini
```
In the first case the engine will log on the console the progress
of the job and the errors, if any, will be clearly visible. This
is the recommended approach for beginners. In the
second case the progress will not be visible but it
can be extracted from the engine database with
the command
```
$ srun oq engine --show-log -1
```
where `-1` denotes the last submitted job. Using `sbatch` is
recommended to users that needs to send multiple calculations. The
calculations might be serialized by the engine queue, depending on the
configuration, but even if the jobs are sequential, the subtasks
spawned by them will run in parallel and make use of all of the
cluster.

NB: by default the engine will use a couple of nodes of the cluster.
You may use more or less resources by setting the parameter
`concurrent_tasks`. For instance, if you want to use around 600
cores you can give the command
```
$ srun oq engine --run job.ini -p concurrent_tasks=600
```

All the usual `oq commands` are available, but you need to prepend
`srun` to them; for instance
```
$ srun oq show performance
```
will give informations about the performance of the last submitted job.

## Running out of quota

Right now the engine store all of its files (intermediate results and
`calc_XXX.hdf5` files) under the `$HOME/oqdata` directory. It is therefore
easy to run out of the quota for large calculations. Fortunaly there
is an environment variable `$OQ_DATADIR` that can be configured to point
to some other target, like a directory on a large shared disk. Such
directory must be accessible in read/write mode from all workers in
the clusters. Another option is to set a `shared_dir` in the
`openquake.cfg` file and then the engine will store its data under the
path `shared_dir/$HOME/oqdata`. This option is preferable since it will
work transparently for all users but only the sysadmin can set it.

## Installing on HPC

This section is for the administrators of the HPC cluster.
Installing the engine requires access to PyPI since the universal
installer will download packages from there. 

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
# pip install -r https://raw.githubusercontent.com/gem/oq-engine/engine-3.18/requirements-py310-linux64.txt
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
