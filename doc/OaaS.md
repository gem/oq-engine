Ideas for OpenQuake as a Service (OaaS)
=======================================

We are interested in assessing the feasibility of a cloud service for
OpenQuake calculations.

The workflow would be as follows:

1. the user posts the inputs of the calculation as a single zip archive
to an OpenQuake server

2. The server allocates a cloud machine (if available) and send the input
to it

3. The cloud machine runs the calculation and when it finishes copies
back the datastore to the server machine, then the machine stops.
The topology is

   User(Laptop) ---> OQServer(GEM machine) <---> Cloud (Azure or other machines)

There are several import points.

1. the OQServer is a long-lived machine exposing the OQ database and the
   webui to show the performed calculations and to run new calculations
2. the OQServer must be able to allocate cloud machines, ideally via a
   Python API or by calling a command line API as a subprocess
3. the cloud machine must be able to communicate with the OQServer via a
   socket in order to be able to write the logs in the database
4. we must manage the case when the cloud machine is not available or
   is available but it dies in the middle of the computation
5. the cloud machine can die because Azure kills it, or we kill it
   because calculation is taking too long, or the calculations runs out
   of memory or out of disk space, or there is a hardware failure
6. in any case there must be NO automatic resubmission of a calculation


Volcano questions
-----------------

- we expect a grid-engine-like interface `qsub script.py arg...`
- we expect a shared filesystem
- Python API: multiprocessing-like with .submit and (possibly) .kill
