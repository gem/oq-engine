# OpenQuake Engine

![OpenQuake Logo](https://github.com/gem/oq-infrastructure/raw/master/logos/oq-logo.png)

The **OpenQuake Engine** is an open source application that allows users to compute **seismic hazard** and **seismic risk** of earthquakes on a global scale. It runs on Linux, macOS and Windows, on laptops, workstations, standalone servers and multi-node clusters. DOI: [10.13117/openquake.engine](https://doi.org/10.13117/openquake.engine)

<!-- GEM BEGIN: apply the following patch with the proper values for the next release
-[![Build Status](https://travis-ci.org/gem/oq-engine.svg?branch=master)](https://travis-ci.org/gem/oq-engine)
 
-### Current stable
+## OpenQuake Engine version 2.6 (Gutenberg)
 
-Current stable version is the **OpenQuake Engine 2.5** 'Fourier'. The documentation is available at https://github.com/gem/oq-engine/tree/engine-2.5#openquake-engine.
-* [What's new](../engine-2.5/doc/whats-new.md)
-
+Starting from OpenQuake version 2.0 we have introduced a "code name" to honour earthquake scientists.
 
+The code name for version 2.6 is **Gutenberg**, in memory of [Beno Gutenberg](https://en.wikipedia.org/wiki/Beno_Gutenberg).
+* [What's new](../engine-2.6/doc/whats-new.md)
+ 
+## Documentation
-## Documentation (master tree)
-->
## OpenQuake Engine version 3.14

* [What's new](./doc/whats-new.md)

### Current LTS release (for users wanting stability)

Current Long Term Support version is the **OpenQuake Engine 3.11** 'Wegener'. The documentation is available at https://github.com/gem/oq-engine/tree/engine-3.11#openquake-engine.

* [What's new](../engine-3.11/doc/whats-new.md)

## Documentation

<!-- GEM END -->

### General overview

* [About](doc/about.md)
* [FAQ](doc/faq.md)
* [Manuals](https://www.globalquakemodel.org/single-post/OpenQuake-Engine-Manual)
* [OQ Commands](doc/adv-manual/oq-commands.rst)
* [Architecture](doc/adv-manual/architecture.rst)
* [Calculation Workflow](doc/calculation-workflow.md)
* [Hardware Suggestions](doc/hardware-suggestions.md)
* [Continuous integration and testing](doc/testing.md)
* [Glossary of Terms](doc/glossary.md)

#### For contributors

* [Development Philosophy and Coding Guidelines](doc/development-guidelines.md)
* [Source Code/API Documentation](http://docs.openquake.org/oq-engine/)
* [HTTP REST API](doc/web-api.md)
* [Implementing a new GSIM](doc/implementing-new-gsim.md)

### Installation

* [Which installation method should I use?](doc/installing/README.md)
* [Installing with the universal installer](doc/installing/universal.md)
* [Installing from Debian packages](doc/installing/ubuntu.md)
* [Installing from RPM packages](doc/installing/rhel.md)
* [Installing from sources](doc/installing/development.md)
* [Installing on a cluster](doc/installing/cluster.md)
* [Installing on Windows](doc/installing/windows.md)
* [Deploy a Docker container](doc/installing/docker.md)

#### Mirrors

A mirror of this repository, hosted in Pavia (Italy), is available at [https://mirror.openquake.org/git/GEM/oq-engine.git](https://mirror.openquake.org/git/GEM/oq-engine.git).

The main download server ([downloads.openquake.org](https://downloads.openquake.org/)) is hosted in Nürnberg (Germany).

### Running the OpenQuake Engine

* [Using the command line](doc/running/unix.md)
* [Using the WebUI](doc/running/server.md)

### Visualizing outputs via QGIS

![IRMT Logo](https://github.com/gem/oq-infrastructure/raw/master/icons/irmt_icon.png)

* [Installation](https://docs.openquake.org/oq-irmt-qgis/latest/00_installation.html)
* [Driving the Engine](https://docs.openquake.org/oq-irmt-qgis/latest/14_driving_the_oqengine.html)
* [Visualizing outputs](https://docs.openquake.org/oq-irmt-qgis/latest/15_viewer_dock.html)
* [Repository](https://plugins.qgis.org/plugins/svir/)
* [Source code](https://github.com/gem/oq-irmt-qgis)

## License

The OpenQuake Engine is released under the **[GNU Affero Public License 3](LICENSE)**.

## Contacts

* Support forum: https://groups.google.com/forum/#!forum/openquake-users
* Twitter: [@gem_devs](https://twitter.com/gem_devs)
* Email: info@openquake.org
* IRC: [irc.freenode.net](https://webchat.freenode.net/), channel #openquake

## Thanks


***


The OpenQuake Engine is developed by the **[Global Earthquake Model Foundation (GEM)](http://gem.foundation)** with the support of

## Public Partners

![](https://github.com/gem/oq-infrastructure/raw/master/logos/public/nerc.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/public/dpc.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/public/gns_science.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/public/aus.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/public/nrcan.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/public/NTU.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/public/nset.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/public/swiss_1.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/public/tem.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/public/usaid.jpg)

## Private Partners

#### Governors
![](https://github.com/gem/oq-infrastructure/raw/master/logos/private/governors/eucentre.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/private/governors/FMGlobal.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/private/governors/hannoverRe.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/private/governors/munichRe.jpg)

![](https://github.com/gem/oq-infrastructure/raw/master/logos/private/governors/swissRe.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/private/governors/verisk.png)


#### Advisors
![](https://github.com/gem/oq-infrastructure/raw/master/logos/private/advisors/axa.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/private/advisors/descartes.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/private/advisors/oneconcern.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/private/advisors/guycarpenter.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/private/advisors/partnerRe.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/private/advisors/global_parametrics.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/private/advisors/safehub.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/private/advisors/wtw.png)


## Associate Partners

![](https://github.com/gem/oq-infrastructure/raw/master/logos/associate/apdim.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/associate/cssc.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/associate/EERI_GEM.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/associate/iaee.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/associate/iaspei.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/associate/IRDRICSU.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/associate/istructe.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/associate/oecd.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/associate/undrr.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/associate/unesco.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/associate/usgs.jpg)


## Project Partners

![](https://github.com/gem/oq-infrastructure/raw/master/logos/project/aon.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/project/sg.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/project/sura.png)


## Products Distribution Partners

![](https://github.com/gem/oq-infrastructure/raw/master/logos/prod_distr/imagecat.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/prod_distr/nasdaq.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/prod_distr/verisk.png)

***


If you would like to help support development of OpenQuake, please contact us at [partnership@globalquakemodel.org](mailto:partnership@globalquakemodel.org).
For more info visit the GEM website at https://www.globalquakemodel.org/partners
