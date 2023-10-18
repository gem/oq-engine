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

### Current Long Term Support (LTS) release - for users wanting stability

Current LTS version is the **OpenQuake Engine 3.16** 'Angela':

The code name for version 3.16 is **Angela**, in memory of the Italian science journalist [Piero Angela](https://en.wikipedia.org/wiki/Piero_Angela).
* [What's new](../engine-3.16/doc/whats-new.md)
* [Documentation 3.16](https://github.com/gem/oq-engine/tree/engine-3.16#openquake-engine)
* [User's manual](https://docs.openquake.org/oq-engine/manual/latest/)


### Latest release - for users needing the latest features

Latest stable version is the **OpenQuake Engine 3.17**.

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

<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Nerc-logo.png" width="15%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/DPC_logo.jpg" width="15%" align="left"  />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Gns-science-logo.jpg" width="10%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Ga@2x.png" width="15%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Canada_Wordmark_2c.jpg" width="15%" />
<br /><br /><br />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Nanyang-Technological-University-NTU.jpg" width="20%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/NSET_logo.png" width="15%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Swiss-logo.jpg" width="15%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/USAID-Identity.png" width="15%" />
<br /><br /><br />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Logomark_color_2t_2_rgb.png" width="15%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/TEM_logo.gif" width="15%" />

## Private Partners

#### Governors
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Allianz_logo.png" width="10%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Aon_logo.png" width="10%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Eucentre_logo.png" width="10%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Fm-global.png" width="10%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Hannover_Re.png" width="10%" />
<br /><br /><br />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/MMC_SEO.jpg" width="10%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Moodys_RMS.png" width="10%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Munich_Re.png" width="10%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Swiss-re-logo.png" width="10%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Verisk_New_Logo.png" width="10%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Wtwlogo.png" width="10%" />


#### Advisors
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Axa_logo.png" width="10%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/CelsiusPro_logo.png" width="10%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Descartes-underwriting-logo.png" width="10%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Oneconcern-topiqs2020-thumbnail-image.png" width="10%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/PartnerRe_logo.png" width="10%" align="left" />
<img src="https://cloud-storage.globalquakemodel.org/public/partners-logo/Safehub_logo.png" width="10%" />

## Associate Partners

<img src="" width="10%" align="left" />
<img src="" width="10%" align="left" />
<img src="" width="10%" align="left" />
<img src="" width="10%" align="left" />
<img src="" width="10%" align="left" />
<img src="" width="10%" align="left" />
<img src="" width="10%" align="left" />
<img src="" width="10%" align="left" />


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
