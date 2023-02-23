# OpenQuake Engine

![OpenQuake Logo](https://raw.githubusercontent.com/gem/oq-infrastructure/master/logos/oq-logo.png)

The **OpenQuake Engine** is an open source application that allows users to compute **seismic hazard** and **seismic risk** of earthquakes on a global scale. DOI: [10.13117/openquake.engine](https://doi.org/10.13117/openquake.engine)

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

[![AGPLv3](https://www.gnu.org/graphics/agplv3-88x31.png)](https://www.gnu.org/licenses/agpl.html)
[![PyPI Version](https://img.shields.io/pypi/v/openquake.engine.svg)](https://pypi.python.org/pypi/openquake.engine)
![PyPI - Wheel](https://img.shields.io/pypi/wheel/openquake.engine.svg)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/gem/oq-engine.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/gem/oq-engine/context:python)

### Current Long Term Support (LTS) release - for users wanting stability

Current LTS version is the **OpenQuake Engine 3.16** 'Angela':

The code name for version 3.16 is **Angela**, in memory of the Italian science journalist [Piero Angela](https://en.wikipedia.org/wiki/Piero_Angela).
* [What's new](../engine-3.16/doc/whats-new.md)
* [Documentation 3.16](https://github.com/gem/oq-engine/tree/engine-3.16#openquake-engine)
* [User's manual](https://docs.openquake.org/oq-engine/manual/latest/)


### Latest release - for users needing the latest features

Latest stable version is the **OpenQuake Engine 3.16**.

<!-- GEM END -->

## General overview

The OpenQuake Engine software provides calculation and assessment of seismic hazard, risk and decision-making tools via the data, methods and standards that are being developed by **[GEM](http://www.globalquakemodel.org)** (Global Earthquake Model) and its collaborators.

* [Installation](doc/installing/README.md)
* [User's manual](https://docs.openquake.org/oq-engine/manual/latest/)
* [Advanced user manual](https://docs.openquake.org/oq-engine/advanced/master/). _Disclaimer: It includes experimental features and is only recommended for users that are already familiar with the user's manual._
* [FAQ](doc/faq.md)
* [Glossary of Terms](doc/glossary.md)


## Running the OpenQuake Engine

* Using the command line [on Windows](doc/running/windows.md)
* Using the command line [on macOS and Linux](doc/running/unix.md)
* [Using the WebUI](doc/running/server.md)

## Visualizing outputs via QGIS

<img src="https://github.com/gem/oq-infrastructure/raw/master/icons/irmt_icon.png" alt="IRMT Logo" width="50" >

A [QGIS plug-in](https://plugins.qgis.org/plugins/svir/) is available for users that would like to visually explore the outputs from the engine. 
Check the documentation for instructions on how to [drive the engine](https://docs.openquake.org/oq-irmt-qgis/latest/14_driving_the_oqengine.html) and [visualize outputs](https://docs.openquake.org/oq-irmt-qgis/latest/15_viewer_dock.html). [Source code](https://github.com/gem/oq-irmt-qgis) also available.

## For developers and contributors

* [Architecture](doc/adv-manual/architecture.rst)
* [Calculation Workflow](doc/calculation-workflow.md)
* [Continuous integration and testing](doc/testing.md)

#### For contributors

* [Development Philosophy and Coding Guidelines](doc/development-guidelines.md)
* [Source Code/API Documentation](http://docs.openquake.org/oq-engine/)
* [HTTP REST API](doc/web-api.md)
* [Implementing a new GSIM](doc/implementing-new-gsim.md)


#### Mirrors

A mirror of this repository, hosted in Pavia (Italy), is available at [https://mirror.openquake.org/git/GEM/oq-engine.git](https://mirror.openquake.org/git/GEM/oq-engine.git).

The main download server ([downloads.openquake.org](https://downloads.openquake.org/)) is hosted in Nürnberg (Germany).


## License

The OpenQuake Engine is released under the **[GNU Affero Public License 3](LICENSE)**.

## Contacts

* Support forum: https://groups.google.com/forum/#!forum/openquake-users
* Twitter: [@gem_devs](https://twitter.com/gem_devs)
* Email: info@openquake.org


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
