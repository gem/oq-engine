%define repo ##_repo_##
%define version ##_version_##
%define release ##_release_##
%define name python-%{repo}

Summary: Computes hazard, risk and socio-economic impact of earthquakes.
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{repo}-%{version}-%{release}.tar.gz
License: AGPL3
Group: Applications/Engineering
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: The GEM OpenQuake team <devops@openquake.org>
Url: http://github.com/gem/oq-engine

Requires: sudo
Requires: numpy
Requires: scipy
Requires: python-amqp
Requires: python-celery
Requires: python-lxml
Requires: python-shapely
Requires: python-psycopg2
Requires: python-django
Requires: python-setuptools
Requires: python-psutil
Requires: python-mock
Requires: python-futures
Requires: rabbitmq-server
Requires: postgresql-server postgis

Requires: python-oq-hazardlib >= 0.15.0
Requires: python-oq-risklib >= 0.8.0

%description

OpenQuake is an open source application that allows users to
compute seismic hazard and seismic risk of earthquakes on a global scale.

Please note: the /usr/bin/oq-engine script requires a celeryconfig.py file in
the PYTHONPATH; when using binary packages, if a celeryconfig.py is not
available the OpenQuake Engine default celeryconfig.py, located in
/usr/share/openquake/engine, is used.

Copyright (C) 2010-2015, GEM Foundation.


%prep
%setup -n %{repo}-%{version}-%{release} -n %{repo}-%{version}-%{release}

%build
python setup.py build

%install
python setup.py install --single-version-externally-managed -O1 --root=%{buildroot} --record=INSTALLED_FILES
# create directories where the files will be located
mkdir -p %{buildroot}/%{_sysconfdir}/openquake
mkdir -p %{buildroot}/%{_datadir}/openquake/engine
install -m 644 celeryconfig.py %{buildroot}/%{_datadir}/openquake/engine
install -m 644 openquake.cfg %{buildroot}/%{_sysconfdir}/openquake

%clean
rm -rf %{buildroot}

%files -f INSTALLED_FILES
%defattr(-,root,root)
%doc README.md LICENSE CONTRIBUTORS.txt docs
%{_datadir}/openquake/engine/celeryconfig.py*
%{_sysconfdir}/openquake/openquake.cfg

