# -*- coding: utf-8 -*-
# vim: syntax=spec
#
# Copyright (C) 2015-2022 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

# Provide a custom prefix for oq
%define _oqprefix /opt/openquake
%define _oqpython %{_oqprefix}/bin
%define _oqvenv %{_oqprefix}/venv
%define _oqbindir %{_oqvenv}/bin
%define _oqlibdir %{_oqvenv}/lib

# Make sure that the proper installation of python is used by macros
%define __python3 %{_oqpython}/python3
%define __python %{__python3}

%define oqstable ##_stable_##
%define oqrepo ##_repo_##
%define oqversion ##_version_##
%define oqrelease ##_release_##
%define oqname python3-%{oqrepo}
%define oqtimestamp ##_timestamp_##
%define oquser openquake

%if %{oqstable} == 1
%define oqformat %{oqrepo}-%{oqversion}
Release: %{oqrelease}
%else
%define oqformat %{oqrepo}-%{oqversion}-%{oqrelease}
Release: %{oqtimestamp}_%{oqrelease}
%endif

# ==========================================
# Descriptions, and metadata for subpackages
# ==========================================

Summary: Computes earthquake hazard and risk
Name: %{oqname}
Version: %{oqversion}
License: AGPLv3
Group: Applications/Engineering
BuildRoot: %{_tmppath}/python-%{oqformat}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: The GEM OpenQuake team <devops@openquake.org>
Url: http://github.com/gem/oq-engine

# =======================
# Source code and patches
# =======================

Source0: %{url}raw.githubusercontent.com/gem/oq-engine/%{oqversion}/install.py

Requires: oq-python3 >= 3.8.0
Requires: sudo systemd

BuildRequires: oq-python3 sed systemd zip

Obsoletes: python-oq-hazardlib python-oq-engine
Provides: python-oq-hazardlib python-oq-engine

%description
OpenQuake is an open source application that allows users to
compute seismic hazard and seismic risk of earthquakes on a global scale.

Copyright (C) 2010-2022 GEM Foundation

%prep
%setup -n %{oqformat}

%build

%pre

# ======================================================
# Installing the built code:
# ======================================================

%install

# As in %%build, remember the current directory
topdir=$(pwd)

# Use a common function to do an install for all our configurations:
InstallEngine() {

  # Switch to the directory with this configuration's built files
  ConfDir=build/$ConfName
  echo STARTING: INSTALL OF OPENQUAKE ENGINE 

  __python install.py server

  popd

  echo FINISHED: INSTALL OF ENGINE
}

InstallEngine 

%post
%systemd_post openquake-dbserver.service
%systemd_post openquake-webui.service

%clean
rm -rf %{buildroot}

%preun
%systemd_preun openquake-dbserver.service
%systemd_preun openquake-webui.service

%postun
%systemd_postun_with_restart openquake-dbserver.service
%systemd_postun_with_restart openquake-webui.service

%files
%defattr(-,root,root)
%attr(0750, openquake, openquake) %dir %{_localstatedir}/lib/openquake
%dir %{_sysconfdir}/openquake
%dir %{_datadir}/openquake
%doc README.md LICENSE CONTRIBUTORS.txt
%doc doc/*.md
%doc doc/img/*
%doc doc/installing/*
%doc doc/running/*
%doc doc/upgrading/*
%config(noreplace) %{_sysconfdir}/openquake/openquake.cfg
%{_oqbindir}/oq
%{_oqlibdir}/python3*/site-packages/openquake*
%{_bindir}/oq
%{_datadir}/openquake/engine
%{_datadir}/applications/oq-engine-webui.desktop
%{_datadir}/pixmaps/openquake.png
%{_unitdir}/openquake-dbserver.service
%{_unitdir}/openquake-webui.service

%changelog
%if %{oqstable} == 1
* %(date -d @%{oqtimestamp} '+%a %b %d %Y') GEM Automatic Packager <gem-autopack@openquake.org> %{oqversion}-%{oqrelease}
– Stable release of %{oqname}
%else
* %(date -d @%{oqtimestamp} '+%a %b %d %Y') GEM Automatic Packager <gem-autopack@openquake.org> %{oqversion}-%{oqtimestamp}_%{oqrelease}
– Unstable release of %{oqname}
%endif
