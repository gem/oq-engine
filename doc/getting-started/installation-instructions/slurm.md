(slurm)=

# Running on a SLURM cluster (experimental)

Most HPC clusters support a scheduler called SLURM (
Simple Linux Utility for Resource Management). The OpenQuake engine
is able to transparently interface with SLURM, thus making it possible
to run a single calculation over multiple nodes of the cluster.

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

1. an error "You can use at most N nodes", where N depends on the
   configuration chosen by your system administrator and can be inferred from
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

If you are stuck in situation 2 you must kill the
SLURM job with the command `scancel JOBID` (JOBID is listed by the
command `$ squeue -u $USER`). If you are stuck in situation 3 for a long
time it can be better to kill the job and
then relaunch the calculation, this time asking for fewer nodes.

## Running out of quota

The engine will store the calculation files in `shared_dir`,
which must be specified in the configuration file and
must be located on a filesystem accessible to all machines of the cluster.
We suggest to periodically purge old calculations, once the results have
been exported.

## Installing on HPC

This section is for the administrators of the HPC cluster.

Here are the installations instructions to create modules for
engine 3.21 assuming you have python3.11 installed as modules.

We recommend choosing a base path for openquake and then installing 
the different versions using the release number, in our example /apps/openquake/3.21.
This will create different modules for different releases

```
# module load python/3.11
# mkdir /apps/openquake
# python3.11 -m venv /apps/openquake/3.21
# source /apps/openquake/3.21/bin/activate
# pip install -U pip
# pip install -r https://github.com/gem/oq-engine/raw/engine-3.21/requirements-py310-linux64.txt
# pip install openquake.engine==3.21
```
Then you have to define the module file. In our cluster it is located in
`/apps/Modules/modulefiles/openquake/3.21`, please use the appropriate
location for your cluster. The content of the file should be the following:
```
#%Module1.0
##
proc ModulesHelp { } {

  puts stderr "\tOpenQuake - loads the OpenQuake environment"
  puts stderr "\n\tThis will add OpenQuake to your PATH environment variable."
}

module-whatis   "loads the OpenQuake 3.21 environment"

set     version         3.21
set     root    /apps/openquake/3.21 

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
num_cores = 128
max_cores = 1024
serialize_jobs = 2
slurm_time = 12:00:00
submit_cmd = sbatch --account=myaccount oq run

[directory]
shared_dir = /home
```
With `serialize_jobs = 2` at most two jobs per user can be run concurrently. You may want to
increase or reduce this number. Each user will have its own database located in
`<shared_dir>/<username>/oqdata/db.sqlite3`. The database will be created automatically the first time the user runs a calculation, or manually with the command `oq engine --upgrade-db`.
