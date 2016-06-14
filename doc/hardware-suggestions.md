We are often asked to recommend hardware configurations for servers and clusters to run the OpenQuake engine.  Obviously this depends very much on the calculations one wishes to perform and the available budget, but here we attempt to provide some general advice, please remember "your milage may vary".

**All product and company names are trademarks™ or registered trademarks© of their respective holders. GEM is is not affiliated with and does not endorse any of the products or companies mentioned on this page.**

A general rule is more GB of RAM and more GHz you have better is. The OpenQuake Engine is designed with an amount of 2GB of RAM per core in mind.

### Single node configuration

Small to medium hazard calculations and small risk calculations can run on a laptop or an equivalent cloud server: 8GB of RAM and 4 cores with several GB of disk space. Using >= 7.2k RPM disks or solid-state drives (SSD) will improve overall performance.

More serious calculations would be better handled by a single server with a hardware RAID support: our "hope" server is a Dell® PowerEdge™ R420 with 12 cores (2 x Intel® Xeon™ E5-2430) 64GB of RAM and 4x2TB disks in a RAID 10 configuration and a hardware RAID controller (Dell® PERC H710).  It is used now primarily to host databases but for a little while it was the best machine we had in Pavia and was used to run calculations too.

### Large scale/multi-node configuration

Our cluster master node "wilson" is a Dell® PowerEdge™ R720 with 16 Xeon cores, 128GB of RAM and RAID arrays, This sort of machine would be able to handle some pretty large calculations as a single server but can also be used as the master node if you find you need to add more machines to form a cluster; so this might be a good starting point if it is compatible with your budget.

For our largest calculations on a continental or global scale we use a cluster composed of "wilson" (see above) acting as a "master" and 4 worker nodes (Dell® PowerEdge™ M915 blades) each with 4x 16 cores AMD® Opteron™ and 128GB of RAM.  Worker nodes do not need much disk since the data is stored in the master filesystem.

Network is made with a link aggregation between four gigabit connections, in most cases a single gigabit connection is enough.
