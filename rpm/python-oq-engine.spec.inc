%define oqstable ##_stable_##
%define oqrepo ##_repo_##
%define oqversion ##_version_##
%define oqrelease ##_release_##
%define oqname python-%{oqrepo}
%define oqtimestamp ##_timestamp_##
%define oquser openquake

Summary: Computes hazard, risk and socio-economic impact of earthquakes
Name: %{oqname}
Version: %{oqversion}
License: AGPLv3
Group: Applications/Engineering
%if %{oqstable} == 1
Release: %{oqrelease}
Source0: %{oqrepo}-%{oqversion}.tar.gz
BuildRoot: %{_tmppath}/%{oqname}-%{oqversion}-buildroot
%else
Release: %{oqtimestamp}_%{oqrelease}
Source0: %{oqrepo}-%{oqversion}-%{oqrelease}.tar.gz
BuildRoot: %{_tmppath}/%{oqname}-%{oqversion}-%{oqrelease}-buildroot
%endif
Prefix: %{_prefix}
BuildArch: noarch
Vendor: The GEM OpenQuake team <devops@openquake.org>
Url: http://github.com/gem/oq-engine

Patch1: openquake.cfg.patch

Requires(pre): shadow-utils

%define common_deps sudo systemd python numpy scipy python-shapely python-psutil python-decorator python-mock python-futures h5py python-amqp python-celery python-django pyshp python-docutils python-requests python-prctl python-gunicorn rabbitmq-server
%define oqlib_deps python-oq-hazardlib >= 0.22.0
%define dev_deps python-nose python-coverage

Requires: %{common_deps}
Requires: %{oqlib_deps}
Requires: %{dev_deps}

# since tests are currently not enabled during the packaging phase, the following build dependencies are not required
#BuildRequires: %{common_deps}
#BuildRequires: %{dev_deps}
#BuildRequires: %{oqlib_deps}

BuildRequires: systemd python-setuptools

Obsoletes: python-oq-risklib
Provides: python-oq-risklib

%description

OpenQuake is an open source application that allows users to
compute seismic hazard and seismic risk of earthquakes on a global scale.

Copyright (C) 2010-2016 GEM Foundation

%pre
getent group %{oquser} >/dev/null || groupadd -r %{oquser}
getent passwd %{oquser} >/dev/null || \
    useradd -r -g %{oquser} -m -d /var/lib/%{oquser} -s /bin/bash \
    -c "The OpenQuake user" %{oquser}
exit 0

%prep
%if %{oqstable} == 1
%setup -n %{oqrepo}-%{oqversion} -n %{oqrepo}-%{oqversion}
%else
%setup -n %{oqrepo}-%{oqversion}-%{oqrelease} -n %{oqrepo}-%{oqversion}-%{oqrelease}
%endif

%patch1 -p1

%build
python setup.py build

%check
#nosetests -v -a '!slow' --with-doctest --with-coverage --cover-package=openquake.engine

%install
sed -i "s/^__version__[  ]*=.*/__version__ = '%{oqversion}-%{oqrelease}'/g" openquake/risklib/__init__.py
python setup.py install --single-version-externally-managed -O1 --root=%{buildroot} --record=INSTALLED_FILES
# create directories where the files will be located
mkdir -p %{buildroot}%{_sysconfdir}/openquake
mkdir -p %{buildroot}%{_datadir}/openquake/engine
mkdir -p %{buildroot}%{_unitdir}
install -m 644 openquake.cfg %{buildroot}/%{_sysconfdir}/openquake
install -m 644 rpm/systemd/openquake-dbserver.service %{buildroot}%{_unitdir}/openquake-dbserver.service
install -m 644 rpm/systemd/openquake-webui.service %{buildroot}%{_unitdir}/openquake-webui.service
install -m 644 rpm/systemd/openquake-celery.service %{buildroot}%{_unitdir}/openquake-celery.service
cp -R demos %{buildroot}/%{_datadir}/openquake/engine
cp -R utils %{buildroot}/%{_datadir}/openquake/engine

%post
%systemd_post openquake-dbserver.service
%systemd_post openquake-webui.service
%systemd_post openquake-celery.service

%clean
rm -rf %{buildroot}

%preun
%systemd_preun openquake-dbserver.service
%systemd_preun openquake-webui.service
%systemd_preun openquake-celery.service

%postun
%systemd_postun_with_restart openquake-dbserver.service
%systemd_postun_with_restart openquake-webui.service
%systemd_postun_with_restart openquake-celery.service

%files -f INSTALLED_FILES
%defattr(-,root,root)
%doc README.md LICENSE CONTRIBUTORS.txt doc
%{_datadir}/openquake/engine
%{_sysconfdir}/openquake/openquake.cfg
%{_unitdir}/openquake-dbserver.service
%{_unitdir}/openquake-webui.service
%{_unitdir}/openquake-celery.service

%changelog
%if %{oqstable} == 1
* %(date -d @%{oqtimestamp} '+%a %b %d %Y') GEM Automatic Packager <gem-autopack@openquake.org> %{oqversion}-%{oqrelease}
– Stable release of %{oqname}
%else
* %(date -d @%{oqtimestamp} '+%a %b %d %Y') GEM Automatic Packager <gem-autopack@openquake.org> %{oqversion}-%{oqtimestamp}_%{oqrelease}
– Unstable release of %{oqname}
%endif
