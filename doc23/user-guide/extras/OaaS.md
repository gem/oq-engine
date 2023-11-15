Ideas for OpenQuake as a Service (OaaS)
=======================================

We are interested in assessing the feasibility of a cloud service for
OpenQuake calculations.

The workflow would be as follows:

1. the user posts the inputs of the calculation as a single zip archive
to an OpenQuake server

2. The server allocates a cloud machine (if available) and send the input
to it

3. The cloud machine runs the calculation and when it finishes it is
deallocated.

The topology is

   User(Laptop) ---> OQServer(GEM machine) <---> Cloud (Azure or other machines)

There are several import points.

1. the OQServer is a long-lived machine exposing the WebUI
2. the OQServer must be able to allocate cloud machines, ideally via a
   Python API or by calling a command line API
3. the cloud machine must be able to communicate with the OQServer via a
   socket in order to be able to write the logs in the database
4. we must manage the case when the cloud machine is not available or
   is available but it dies in the middle of the computation
5. the cloud machine can die because Azure kills it, or we kill it
   because calculation is taking too long, or the calculations runs out
   of memory or out of disk space, or there is a hardware failure
6. in any case there must be NO automatic resubmission of a calculation

Configuration of server and workers
-----------------------------------

The server machine will have a `devel_server` installation with a
single user (openquake). Moreover it will share the following
directories to the workers: ``` /opt/openquake: shared read-only
/var/lib/openquake: shared read-write ``` The workers *will not have
the engine installed*; they just need to have basic system
libraries and to *mount /opt/openquake*. That guarantees that the
engine versions will always be the same between server and workers.
If the versions were different, it could become impossible to dowload
the results!

Since the file `openquake.cfg` lives in `/opt/openquake` then the
workers will automatically get the address of the database and the
authkey:
```
[dbserver]
host = [name/IP of the server]
authkey = changeme
```
I will also be necessary to configure three directories in the
`openquake.cfg` file:
```
[directory]
shared_dir = /opt/openquake
mosaic_dir = /opt/openquake/mosaic
custom_tmp = /op/openquake/tmp
```
The `mosaic_dir` and `custom_tmp` directories must subdirectories of
`shared_dir`; in this way the workers will be able to read the models
and the other input files.

The `custom_tmp` directory is used to zip and unzip files: zip the
outputs at download time and unzip the inputs at start time. Actually
the WebUI is designed so that the received archives are unzipped in
directories of kind
```
/opt/openquake/tmp/calc_XXX
```
where `XXX` is the number of the calculation being executed.

The `custom_tmp` *must be cleaned up periodically* to avoid running
out of disk space. After a calculation started, the inputs
can be safely removed since they are copied in the datastore
and a calculation can always be repeated.

On top of these directories, there are two other essential directories:
```
/opt/openquake/venv
/opt/openquake/oqdata
```
They both must be subdirectories of the `shared_dir`;
`/opt/openquake/venv` stores the source code and `/opt/openquake/oqdata`
the database and the .hdf5 calculation files.
