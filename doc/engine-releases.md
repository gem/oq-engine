Engine releases
===========================

Since March 2021 engine releases are divided in two categories:
Long Term Support (**LTS**) releases and non-LTS releases.

The plan is to make one LTS release per year. *LTS releases* are ideal
for people that value stability and do not want upgrade the engine
often. They are also ideal for beginners and for everybody not needing
the latest features.

When making a LTS release GEM carefully tests also additional tools,
like the QGIS plugin and the Input Preparation Toolkit (IPT). Moreover
we also release Linux packages and a Windows installer.

An LTS release is supported for one year, until the new LTS comes out,
and we guarantee not to change the datastore format between bug fix
releases. For instance version 3.11 has already had 3 bug fix releases
3.11.1, 3.11.2, 3.11.3 and more are coming. All 3.11.x releases have a
compatibile inner format.

*Non-LTS releases* are for people that need to stay updated with the latest
engine developments. The plan is to make one non-LTS release every 2-3
months. For instance, a scientist contributing a new GMPE to hazardlib
can install a non-LTS release and have the new GMPE in a short time,
without needing to wait one year. People running
large calculations may also want to use an non-LTS release, since
they may need optizations available in the non-LTS, without waiting an
year for the LTS.

The other side of the coin is that short term releases will receive
few bug fixes, i.e. it is more likely that we will release an engine
3.13 rather than an engine 3.12.1, if engine 3.12 is a non-LTS
release. The format of the datastore is not guaranteed to stay
unchanged across major releases, so SRS users must be careful about
that. 

The recommended way to install an SRS release is via the
universal installer (see
https://github.com/gem/oq-engine/blob/master/doc/installing/universal.md)
and we do not provide Linux packages nor Windows installer.

While we try very hard to ensure that the QGIS plugin and the web
tools (like IPT) also work with SRS releases, we do not guarantee
that. For the non-LTS releases a timely delivery of a new engine feature
is more important than having perfect compatibility with IPT and the
QGIS plugin.
