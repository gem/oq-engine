# -*- coding: utf-8 -*-
# vim: syntax=spec
#
# Copyright (C) 2015-2017 GEM Foundation
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

%define oqstable ##_stable_##
%define oqrepo ##_repo_##
%define oqversion ##_version_##
%define oqrelease ##_release_##
%define oqname python-%{oqrepo}
%define oqtimestamp ##_timestamp_##
%define oqprefix /opt/openquake
%define oquser openquake

%if %{oqstable} == 1
%define oqformat %{oqrepo}-%{oqversion}
Release: %{oqrelease}
%else
%define oqformat %{oqrepo}-%{oqversion}-%{oqrelease}
Release: %{oqtimestamp}_%{oqrelease}
%endif

Summary: Computes earthquake hazard and risk
Name: %{oqname}
Version: %{oqversion}
License: AGPLv3
Group: Applications/Engineering
Source0: %{oqformat}.tar.gz
BuildRoot: %{_tmppath}/python-%{oqformat}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: The GEM OpenQuake team <devops@openquake.org>
Url: http://github.com/gem/oq-engine

Patch1: openquake.cfg.patch

Requires(pre): shadow-utils

Requires: python-oq-libs >= 1.5.0
Requires: sudo systemd python

BuildRequires: systemd python-setuptools zip

Obsoletes: python-oq-risklib python-oq-hazardlib
Provides: python-oq-risklib python-oq-hazardlib

%description
OpenQuake is an open source application that allows users to
compute seismic hazard and seismic risk of earthquakes on a global scale.

Copyright (C) 2010-2017 GEM Foundation

%package master
Summary: OpenQuake Engine multi-node cluster support (master node)
Group: Applications/Engineering
Requires: %{name} = %{version}-%{release} rabbitmq-server

%description master
OpenQuake Engine multi-node cluster support (master node)

OpenQuake is an open source application that allows users to
compute seismic hazard and seismic risk of earthquakes on a global scale.

Copyright (C) 2010-2017 GEM Foundation

%package worker
Summary: OpenQuake Engine multi-node cluster support (worker node)
Group: Applications/Engineering
Requires: %{name} = %{version}-%{release}

%description worker
OpenQuake Engine multi-node cluster support (worker node)

OpenQuake is an open source application that allows users to
compute seismic hazard and seismic risk of earthquakes on a global scale.

Copyright (C) 2010-2017 GEM Foundation

%prep
%setup -n %{oqformat}

%patch1 -p1

%build
python setup.py build

%check
#nosetests -v -a '!slow' --with-doctest --with-coverage --cover-package=openquake.engine

%pre
getent group %{oquser} >/dev/null || groupadd -r %{oquser}
getent passwd %{oquser} >/dev/null || \
    useradd -r -g %{oquser} -d %{_localstatedir}/lib/%{oquser} -s /bin/bash \
    -c "The OpenQuake user" %{oquser}

%install
sed -i "s/^__version__[  ]*=.*/__version__ = '%{oqversion}-%{oqrelease}'/g" openquake/baselib/__init__.py
install -p -m 755 -d %{buildroot}%{_bindir}
install -p -m 755 -d %{buildroot}%{oqprefix}/bin
python setup.py install --single-version-externally-managed -O1 --root=%{buildroot} --prefix=%{oqprefix} --install-scripts=%{oqprefix}/bin
ln -sf %{oqprefix}/bin/oq %{buildroot}%{_bindir}/oq
# create directories where the files will be located
mkdir -p %{buildroot}%{_localstatedir}/lib/openquake
mkdir -p %{buildroot}%{_sysconfdir}/openquake
mkdir -p %{buildroot}%{_datadir}/openquake/engine
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/pixmaps
mkdir -p %{buildroot}%{_unitdir}
install -m 644 openquake/engine/openquake.cfg %{buildroot}/%{_sysconfdir}/openquake
install -m 644 debian/desktop/oq-engine-webui.desktop %{buildroot}%{_datadir}/applications
install -m 644 debian/desktop/openquake.png %{buildroot}%{_datadir}/pixmaps
install -m 644 rpm/systemd/openquake-dbserver.service %{buildroot}%{_unitdir}/openquake-dbserver.service
install -m 644 rpm/systemd/openquake-webui.service %{buildroot}%{_unitdir}/openquake-webui.service
install -m 644 rpm/systemd/openquake-celery.service %{buildroot}%{_unitdir}/openquake-celery.service
cp -R demos %{buildroot}/%{_datadir}/openquake/engine
# Make a zipped copy of each demo
helpers/zipdemos.sh %{buildroot}%{_datadir}/openquake/engine/demos
cp -R utils %{buildroot}/%{_datadir}/openquake/engine

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
%attr(0750, openquake, openquake) %dir %{_localstatedir}/lib/openquake
%defattr(-,root,root)
%doc README.md LICENSE CONTRIBUTORS.txt
%doc doc/*.md
%doc doc/img/*
%doc doc/installing/*
%doc doc/running/*
%doc doc/upgrading/*
%config(noreplace) %{_sysconfdir}/openquake/openquake.cfg
%{oqprefix}/bin/oq
%{oqprefix}/lib/python2.7/site-packages/openquake*
%{_bindir}/oq
%{_datadir}/openquake/engine
%{_datadir}/applications/oq-engine-webui.desktop
%{_datadir}/pixmaps/openquake.png
%{_unitdir}/openquake-dbserver.service
%{_unitdir}/openquake-webui.service

%post master
(if ! rabbitmqctl status &>/dev/null; then
    systemctl start rabbitmq-server.service
    rabbit_started=true
fi
if ! rabbitmqctl list_users | grep %{oquser}; then
    rabbitmqctl add_user %{oquser} %{oquser}
fi
if ! rabbitmqctl list_vhosts | grep %{oquser}; then
    rabbitmqctl add_vhost %{oquser}
    rabbitmqctl set_permissions -p %{oquser} %{oquser} ".*" ".*" ".*"
fi
if $rabbit_started; then
    systemctl stop rabbitmq-server.service
fi
) >/dev/null || true

%files master

%post worker
%systemd_post openquake-celery.service

%preun worker
%systemd_preun openquake-celery.service

%postun worker
%systemd_postun_with_restart openquake-celery.service

%files worker
%{_unitdir}/openquake-celery.service

%changelog
%if %{oqstable} == 1
* %(date -d @%{oqtimestamp} '+%a %b %d %Y') GEM Automatic Packager <gem-autopack@openquake.org> %{oqversion}-%{oqrelease}
– Stable release of %{oqname}
%else
* %(date -d @%{oqtimestamp} '+%a %b %d %Y') GEM Automatic Packager <gem-autopack@openquake.org> %{oqversion}-%{oqtimestamp}_%{oqrelease}
– Unstable release of %{oqname}
%endif
