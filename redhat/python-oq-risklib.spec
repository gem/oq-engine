%define repo ##_repo_##
%define version ##_version_##
%define release ##_release_##
%define name python-%{repo}

Summary: oq-risklib is a library for performing seismic risk analysis
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{repo}-%{version}-%{release}.tar.gz
License: AGPL3
Group: Applications/Engineering
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: GEM Foundation <devops@openquake.org>
Url: http://github.com/gem/oq-risklib

%define common_deps python numpy scipy python-shapely python-psutil python-lxml python-futures h5py
%define oqlib_deps python-oq-hazardlib >= 0.15.0
Requires: %{common_deps}
Requires: %{oqlib_deps}

BuildRequires: %{common_deps}
BuildRequires: %{oqlib_deps}
BuildRequires: python-setuptools
BuildRequires: python-nose
BuildRequires: python-mock
BuildRequires: python-coverage


%description
OpenQuake Risk Library (oq-risklib)
-----------------------------------

OpenQuake Risklib is an open source library for seismic risk assessment,
which includes several modules capable of calculating losses and damage
distributions for a scenario earthquake, or for calculating probabilistic
risk from all the possible events that might occur in a region within a
certain time span (that can be estimated through an event-based approach,
or a classical PSHA-based approach). The main outputs of this library are
loss statistics, loss maps, loss curves, damage distributions and collapse
maps.

The GEM Foundation (http://www.globalquakemodel.org/) supports the development
of this library by adding the most common methodologies used by seismic risk
modellers. Comments, suggestions and criticisms from the community are always
very welcome.

Copyright (C) 2013-2015, GEM Foundation.


%prep
%setup -n %{repo}-%{version}-%{release} -n %{repo}-%{version}-%{release}

%build
python setup.py build

%check
PYTHONPATH="$(pwd)" nosetests -a '!slow,' -v --with-doctest --with-coverage --cover-package=openquake.baselib --cover-package=openquake.risklib --cover-package=openquake.commonlib

%install
python setup.py install --single-version-externally-managed -O1 --root=%{buildroot} --record=INSTALLED_FILES

%clean
rm -rf %{buildroot}

%files -f INSTALLED_FILES
%defattr(-,root,root)
%doc LICENSE README.md doc demos
