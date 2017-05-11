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

Requires: python-oq-libs >= 1.0.0 python-oq-hazardlib >= 0.24.0
Requires: sudo systemd python

BuildRequires: systemd python-setuptools

Obsoletes: python-oq-risklib
Provides: python-oq-risklib

%description
OpenQuake is an open source application that allows users to
compute seismic hazard and seismic risk of earthquakes on a global scale.

Copyright (C) 2010-2017 GEM Foundation

%package master
Summary: OpenQuake Engine multi-node cluster support (master node)
Group: Applications/Engineering
Requires: %{name}%{?_isa} = %{version}-%{release} rabbitmq-server

%description master
OpenQuake Engine multi-node cluster support (master node)

OpenQuake is an open source application that allows users to
compute seismic hazard and seismic risk of earthquakes on a global scale.

Copyright (C) 2010-2017 GEM Foundation

%package worker
Summary: OpenQuake Engine multi-node cluster support (worker node)
Group: Applications/Engineering
Requires: %{name}%{?_isa} = %{version}-%{release}

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
    useradd -r -g %{oquser} -m -d /var/lib/%{oquser} -s /bin/bash \
    -c "The OpenQuake user" %{oquser}

%install
sed -i "s/^__version__[  ]*=.*/__version__ = '%{oqversion}-%{oqrelease}'/g" openquake/risklib/__init__.py
install -p -m 755 -d %{buildroot}%{_bindir}
install -p -m 755 -d %{buildroot}%{oqprefix}/bin
python setup.py install --single-version-externally-managed -O1 --root=%{buildroot} --prefix=%{oqprefix} --install-scripts=%{oqprefix}/bin
ln -sf %{oqprefix}/bin/oq %{buildroot}%{_bindir}/oq
# create directories where the files will be located
mkdir -p %{buildroot}%{_sysconfdir}/openquake
mkdir -p %{buildroot}%{_datadir}/openquake/engine
mkdir -p %{buildroot}%{_unitdir}
install -m 644 openquake/engine/openquake.cfg %{buildroot}/%{_sysconfdir}/openquake
install -m 644 debian/desktop/oq-engine-webui.desktop %{buildroot}/%{_datadir}/applications
install -m 644 debian/desktop/openquake.png %{buildroot}/%{_datadir}/pixmaps
install -m 644 rpm/systemd/openquake-dbserver.service %{buildroot}%{_unitdir}/openquake-dbserver.service
install -m 644 rpm/systemd/openquake-webui.service %{buildroot}%{_unitdir}/openquake-webui.service
install -m 644 rpm/systemd/openquake-celery.service %{buildroot}%{_unitdir}/openquake-celery.service
cp -R demos %{buildroot}/%{_datadir}/openquake/engine
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
%defattr(-,root,root)
%doc README.md LICENSE CONTRIBUTORS.txt
%doc doc/*.md
%doc doc/img/*
%doc doc/installing/*
%doc doc/running/*
%doc doc/upgrading/*
%{oqprefix}/bin/oq
%{oqprefix}/lib/python2.7/site-packages/openquake*
%{_bindir}/oq
%{_datadir}/openquake/engine
%{_sysconfdir}/openquake/openquake.cfg
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
