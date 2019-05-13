# OpenQuake Engine

![OpenQuake Logo](https://github.com/gem/oq-infrastructure/raw/master/logos/oq-logo.png)

The **OpenQuake Engine** is an open source application that allows users to compute **seismic hazard** and **seismic risk** of earthquakes on a global scale. It runs on Linux, macOS and Windows, on laptops, workstations, standalone servers and multi-node clusters.

<!-- GEM BEGIN: apply the following patch with the proper values for the next release
-[![Build Status](https://travis-ci.org/gem/oq-engine.svg?branch=master)](https://travis-ci.org/gem/oq-engine)
 
-### Current stable
+## OpenQuake Engine version 2.6 (Gutenberg)
 
-Current stable version is the **OpenQuake Engine 2.5** 'Fourier'. The documentation is available at https://github.com/gem/oq-engine/tree/engine-2.5#openquake-engine.
-* [What's new](https://github.com/gem/oq-engine/blob/engine-2.5/doc/whats-new.md)
-
+Starting from OpenQuake version 2.0 we have introduced a "code name" to honour earthquake scientists.
 
+The code name for version 2.6 is **Gutenberg**, in memory of [Beno Gutenberg](https://en.wikipedia.org/wiki/Beno_Gutenberg).
+* [What's new](https://github.com/gem/oq-engine/blob/engine-2.6/doc/whats-new.md)
+ 
+## Documentation
-## Documentation (master tree)
-->
## OpenQuake Engine version 3.5 (Palmieri)

Starting from OpenQuake version 2.0 we have introduced a "code name" to honour earthquake scientists.

The code name for version 3.5 is **Palmieri**, in memory of [Luigi Palmieri](https://en.wikipedia.org/wiki/Luigi_Palmieri).

* [What's new](https://github.com/gem/oq-engine/blob/engine-3.5/doc/whats-new.md)

## Documentation

<!-- GEM END -->

### General overview

* [About](https://github.com/gem/oq-engine/blob/engine-3.5/doc/about.md)
* [FAQ](https://github.com/gem/oq-engine/blob/engine-3.5/doc/faq.md)
* [Manuals](https://www.globalquakemodel.org/single-post/OpenQuake-Engine-Manual)
* [OQ Commands](https://github.com/gem/oq-engine/blob/engine-3.5/doc/oq-commands.md)
* [Architecture](https://github.com/gem/oq-engine/blob/engine-3.5/doc/sphinx/architecture.rst)
* [Calculation Workflow](https://github.com/gem/oq-engine/blob/engine-3.5/doc/calculation-workflow.md)
* [Hardware Suggestions](https://github.com/gem/oq-engine/blob/engine-3.5/doc/hardware-suggestions.md)
* [Continuous integration and testing](https://github.com/gem/oq-engine/blob/engine-3.5/doc/testing.md)
* [Glossary of Terms](https://github.com/gem/oq-engine/blob/engine-3.5/doc/glossary.md)

#### For contributors

* [Development Philosophy and Coding Guidelines](https://github.com/gem/oq-engine/blob/engine-3.5/doc/development-guidelines.md)
* [Source Code/API Documentation](http://docs.openquake.org/oq-engine/)
* [HTTP REST API](https://github.com/gem/oq-engine/blob/engine-3.5/doc/web-api.md)
* [Implementing a new GSIM](https://github.com/gem/oq-engine/blob/engine-3.5/doc/implementing-new-gsim.md)

### Installation

* [Technology stack and requirements](https://github.com/gem/oq-engine/blob/engine-3.5/doc/requirements.md)
* [Which installation method should I use?](https://github.com/gem/oq-engine/blob/engine-3.5/doc/installing/overview.md)

#### Linux

* [Installing on Ubuntu](https://github.com/gem/oq-engine/blob/engine-3.5/doc/installing/ubuntu.md)
* [Installing on RedHat and derivatives](https://github.com/gem/oq-engine/blob/engine-3.5/doc/installing/rhel.md)
* [Installing on other flavors (without sudo)](https://github.com/gem/oq-engine/blob/engine-3.5/doc/installing/linux-generic.md)
* [Installing from sources](https://github.com/gem/oq-engine/blob/engine-3.5/doc/installing/development.md)
* [Installing on a cluster](https://github.com/gem/oq-engine/blob/engine-3.5/doc/installing/cluster.md)

#### macOS

* [Installing on macOS](https://github.com/gem/oq-engine/blob/engine-3.5/doc/installing/macos.md)
* [Installing from sources](https://github.com/gem/oq-engine/blob/engine-3.5/doc/installing/development.md#macos)

#### Windows

* [Installing on Windows](https://github.com/gem/oq-engine/blob/engine-3.5/doc/installing/windows.md)
* [Starting the software](https://github.com/gem/oq-engine/blob/engine-3.5/doc/running/windows.md)

#### VirtualBox

* [Download OVA appliance](https://downloads.openquake.org/ova/stable/)

#### Cloud

* [Deploy a Docker container](https://github.com/gem/oq-engine/blob/engine-3.5/doc/installing/docker.md)

### Running the OpenQuake Engine

* [Using the command line](https://github.com/gem/oq-engine/blob/engine-3.5/doc/running/unix.md)
* [Using the WebUI](https://github.com/gem/oq-engine/blob/engine-3.5/doc/running/server.md)

### Visualizing outputs via QGIS

![IRMT Logo](https://github.com/gem/oq-infrastructure/raw/master/icons/irmt_icon.png)

* [Installation](https://docs.openquake.org/oq-irmt-qgis/latest/00_installation.html)
* [Driving the Engine](https://docs.openquake.org/oq-irmt-qgis/latest/14_driving_the_oqengine.html)
* [Visualizing outputs](https://docs.openquake.org/oq-irmt-qgis/latest/15_viewer_dock.html)
* [Source code](https://github.com/gem/oq-irmt-qgis)

## License

The OpenQuake Engine is released under the **[GNU Affero Public License 3](https://github.com/gem/oq-engine/blob/engine-3.5/LICENSE)**.

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
