We are often asked to recommend hardware configurations for servers and clusters to run the OpenQuake engine.  Obviously this depends very much on the calculations one wishes to perform and the available budget, but here we attempt to provide some general advice. Please remember that "your mileage may vary".

A general rule is the more GB of RAM and the more GHz you have, the better it is. The OpenQuake Engine is designed with a suggested amount of 2GB of RAM per worker core for classical, 4GB of RAM for event based computations. In a cluster the controller node requires more RAM than the worker nodes.

### Single node configuration

Small to medium hazard calculations and small risk calculations can run on a laptop or an equivalent cloud server: 8GB of RAM and 4  physical cores with several GB of disk space.

Recent processor have a large number of threads but often not enough
memory, i.e. less than 2 GB per thread. In that case it is recommended
to disable hyperthreading, if possible. Otherwise, you can edit the
openquake.cfg file and reduce the number of (virtual) cores used by
the engine, thus saving memory at the cost of reducing the performance.
Please consider buying a memory expansion instead.

More serious calculations would be better handled by a powerful server. In spring 2022 we bought a single server with 128 AMD Epyc Rome CPUs and 512 GB of RAM. This is the best machine we have. Even half of such specs are enough for running most hazard models.

### Multi-node configuration

Configuring a cluster is complex and the engine is currently less efficient in a multi-node configuration due to the problem of slow tasks, i.e. the entire calculation is waiting for the slowest task to
finish. Given the same number of cores it is much better to use a single machine rather than a cluster.

Our cluster master node "wilson" is a Dell® PowerEdge™ R720 with 16 Xeon cores, 128GB of RAM RAID arrays and 10Gbit/s networking. This sort of machine would be able to handle some pretty large calculations as a single server but can also be used as the master node if you find you need to add more machines to form a cluster; so this might be a good starting point if it is compatible with your budget.

For our largest calculations on a continental or global scale we use a cluster composed of "wilson" (see above) acting as a "master" and two clusters composed by 5 worker nodes (Dell® PowerEdge™ M915 blades) each with 4x 16 cores AMD® Opteron™ and 128GB of RAM for the first and 4 Dell® PowerEdge™ M630 blades (2x 20t/10c Intel® Xeon™ E5-2640v4, 128GB RAM each) for the second cluster.  Worker nodes do not need much disk since the data is stored in the master filesystem.

Network is made with a link aggregation between two 10 gigabit connections; however, up to a couple hundred workers a single gigabit connection is enough.

Windows is not supported for large scale deployments.

### Cloud

The OpenQuake Engine can be deployed in the Cloud a virtual machine (using standard [Ubuntu](installing/ubuntu.md) or [RHEL/CentOS](installing/rhel.md) binary packages) or using [Docker containers](installing/docker.md). Both single node and multi-node configuration are supported.

Deployment can considered stateless (an "always-on" configuration isn't required) as soon as outputs have been exported via the [REST API](running/server.md) or via the [CLI](running/unix.md).

Our users reported to have successfully deployed the OpenQuake Engine on [Amazon AWS](https://aws.amazon.com/), [Google GCE](https://cloud.google.com/compute/), [Microsoft Azure](https://azure.microsoft.com/), [OpenStack IaaS](https://www.openstack.org/) and many other providers or internal platforms.

Here a couple of links you may find useful:

https://aws.amazon.com/blogs/compute/disabling-intel-hyper-threading-technology-on-amazon-linux/

https://learn.microsoft.com/en-us/azure/virtual-machines/acu

***

**All product and company names are trademarks™ or registered trademarks© of their respective holders.**

## Getting help
If you need help or have questions/comments/feedback for us, you can subscribe to the OpenQuake users mailing list: https://groups.google.com/g/openquake-users
