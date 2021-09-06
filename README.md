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

## OpenQuake Engine version 3.12

* [What's new](./doc/whats-new.md)

### Current LTS release

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

* [Technology stack and requirements](doc/requirements.md)
* [Which installation method should I use?](doc/installing/README.md)

#### Linux

* [Installing on Ubuntu](doc/installing/ubuntu.md)
* [Installing on RedHat and derivatives](doc/installing/rhel.md)
* [Installing on other flavors (without sudo)](doc/installing/linux-generic.md)
* [Installing from sources](doc/installing/development.md)
* [Installing on a cluster](doc/installing/cluster.md)

#### macOS

* [Installing on macOS](doc/installing/macos.md)
* [Installing from sources](doc/installing/development.md#macos)

#### Windows

* [Installing on Windows](doc/installing/windows.md)
* [Installing from sources](doc/installing/development-windows.md)
* [Starting the software](doc/running/windows.md)

#### Cloud

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

The OpenQuake Engine is developed by the **[Global Earthquake Model Foundation (GEM)](http://gem.foundation)** with the support of
![](https://github.com/gem/oq-infrastructure/raw/master/logos/aus.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/cidigen.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/sg_170x104.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/gfz.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/pcn.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/nied.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/nset.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/morst.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/RCN.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/swiss_1.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/tem.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/TCIP-01.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/nerc.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/usaid_BsOsE8Z_QZnaG6c.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/FUNVISIS_GEM_logo.png)

***

![](https://github.com/gem/oq-infrastructure/raw/master/logos/FMGlobal.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/hannoverRe.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/Nephila.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/munichre_HwOCwR4.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/zurich_3eh504q.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/Air_JlQh6Ke.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/sur_170x104.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/EUCENTRE_BRAw8x4.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/GiroJ.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/arup.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/OYO_1.jpg)

***

![](https://github.com/gem/oq-infrastructure/raw/master/logos/OECD.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/worldbank_2.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/ISDR.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/Unesco.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/iaspei.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/iaee.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/istructe.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/cssc.jpg)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/IRDRICSU.png)
![](https://github.com/gem/oq-infrastructure/raw/master/logos/EERI_GEM.png)

If you would like to help support development of OpenQuake, please contact us at [partnership@globalquakemodel.org](mailto:partnership@globalquakemodel.org).
For more info visit the GEM website at https://www.globalquakemodel.org/partners
