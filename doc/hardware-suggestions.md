We are often asked to recommend hardware configurations for servers and clusters to run the OpenQuake engine.  Obviously this depends very much on the calculations one wishes to perform and the available budget, but here we attempt to provide some general advice, please remember "your milage may vary".

**All product and company names are trademarks™ or registered trademarks© of their respective holders.**

A general rule is more GB of RAM and more GHz you have better is. The OpenQuake Engine is designed with an amount of 2GB of RAM per worker core in mind. In the controller it is best to have more RAM.

### Single node configuration

Small to medium hazard calculations and small risk calculations can run on a laptop or an equivalent cloud server: 8GB of RAM and 4 cores with several GB of disk space. Using >= 7.2k RPM disks or solid-state drives (SSD) will improve the overall performance.

More serious calculations would be better handled by a single server with a hardware RAID support: our "hope" server is a Dell® PowerEdge™ R420 with 12 cores (2 x Intel® Xeon™ E5-2430) 64GB of RAM and 4x2TB disks in a RAID 10 configuration and a hardware RAID controller (Dell® PERC H710).  It is used now primarily to host databases but for a little while it was the best machine we had in Pavia and was used to run calculations too.

### Large scale/multi-node configuration

Our cluster master node "wilson" is a Dell® PowerEdge™ R720 with 16 Xeon cores, 128GB of RAM RAID arrays and 10Gbit/s networking. This sort of machine would be able to handle some pretty large calculations as a single server but can also be used as the master node if you find you need to add more machines to form a cluster; so this might be a good starting point if it is compatible with your budget.

For our largest calculations on a continental or global scale we use a cluster composed of "wilson" (see above) acting as a "master" and two clusters composed by 5 worker nodes (Dell® PowerEdge™ M915 blades) each with 4x 16 cores AMD® Opteron™ and 128GB of RAM for the first and 4 Dell® PowerEdge™ M630 blades (2x 20t/10c Intel® Xeon™ E5-2640v4, 128GB RAM each) for the second cluster.  Worker nodes do not need much disk since the data is stored in the master filesystem.

Network is made with a link aggregation between two 10 gigabit connections; however, up to a couple hundred celery workers a single gigabit connection is enough.

Windows is not supported for large scale deployments.

### Cloud

The OpenQuake Engine can be deployed in the Cloud a virtual machine (using standard [Ubuntu](installing/ubuntu.md) or [RHEL/CentOS](installing/rhel.md) binary packages) or using [Docker containers](installing/docker.md). Both single node and multi-node configuration are supported.

Deployment can considered stateless (an "always-on" configuration isn't required) as soon as outputs have been exported via the [REST API](running/server.md) or via the [CLI](running/unix.md).

Our users reported to have successfully deployed the OpenQuake Engine on [Amazon AWS](https://aws.amazon.com/), [Google GCE](https://cloud.google.com/compute/), [Microsoft Azure](https://azure.microsoft.com/), [OpenStack IaaS](https://www.openstack.org/) and many other providers or internal platforms.

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
