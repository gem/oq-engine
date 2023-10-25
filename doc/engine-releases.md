Engine releases
===========================

Since March 2021 engine releases are divided in two categories:
Long Term Support (**LTS**) releases and non-LTS releases.

The plan is to make a few LTS releases (one every 1-2 years). *LTS
releases* are ideal for people that value stability and do not want to
upgrade the engine often. They are also ideal for beginners and for
everybody not needing the latest features.

When making a LTS release GEM carefully tests also additional tools,
like the QGIS plugin and the Input Preparation Toolkit (IPT). Moreover
we also release Linux packages and a Windows installer.

An LTS release is supported until the new LTS comes out,
and we guarantee not to change the datastore format between bug fix
releases. For instance version 3.11 has already had 4 bug fix releases
3.11.1, 3.11.2, 3.11.3, 3.11.4. All 3.11.x releases have a
compatible inner format.

*Non-LTS releases* are for people that need to stay updated with the latest
engine developments. The plan is to make one non-LTS release every 2-3
months. For instance, a scientist contributing a new GMPE to hazardlib
can install a non-LTS release and have the new GMPE in a short time,
without needing to wait one or two years. People running
large calculations may also want to use an non-LTS release, since
they may need optizations available in the non-LTS, without waiting
years for the LTS.

Short term releases will likely receive few bug fixes, i.e. it is more likely
that we will release an engine 3.13 rather than an engine 3.12.1, if
engine 3.12 is a non-LTS release. The format of the datastore is not
guaranteed to stay unchanged across major releases, so non-LTS users must
be careful about that.

The recommended way to install a non-LTS release is via the
universal installer (see
https://github.com/gem/oq-engine/blob/engine-3.18/doc/installing/universal.md)
and we do not provide Linux packages nor Windows installer.

While we try very hard to ensure that the QGIS plugin and the web
tools (like IPT) also work with non-LTS releases, we do not guarantee
that. For non-LTS releases a timely delivery of new engine features
is more important than having perfect compatibility with IPT and/or the
QGIS plugin.
