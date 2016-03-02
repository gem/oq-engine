%define oqrepo ##_repo_##
%define oqversion ##_version_##
%define oqrelease ##_release_##
%define oqname python-%{oqrepo}
%define oqtimestamp ##_timestamp_##

Summary: oq-risklib is a library for performing seismic risk analysis
Name: %{oqname}
Version: %{oqversion}
Release: %{oqtimestamp}_%{oqrelease}
Source0: %{oqrepo}-%{oqversion}-%{oqrelease}.tar.gz
License: AGPLv3
Group: Applications/Engineering
BuildRoot: %{_tmppath}/%{oqname}-%{oqversion}-%{oqrelease}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: GEM Foundation <devops@openquake.org>
Url: http://github.com/gem/oq-risklib

%define common_deps python numpy scipy python-shapely python-psutil python-futures python-decorator python-mock python-prctl h5py
%define oqlib_deps python-oq-hazardlib >= 0.20.0
%define dev_deps python-nose python-coverage

Requires: %{common_deps}
Requires: %{oqlib_deps}
Requires: %{dev_deps}

# Since tests are currently not enabled during the packaging phase, the following build dependencies are not required
#BuildRequires: %{common_deps}
#BuildRequires: %{dev_deps}
#BuildRequires: %{oqlib_deps}

BuildRequires: python-setuptools

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

Copyright (C) 2013-2016 GEM Foundation


%prep
%setup -n %{oqrepo}-%{oqversion}-%{oqrelease} -n %{oqrepo}-%{oqversion}-%{oqrelease}

%build
python setup.py build

%check
#PYTHONPATH="$(pwd)" nosetests -a '!slow,' -v --with-doctest --with-coverage --cover-package=openquake.baselib --cover-package=openquake.risklib --cover-package=openquake.commonlib

%install
python setup.py install --single-version-externally-managed -O1 --root=%{buildroot} --record=INSTALLED_FILES
mkdir -p %{buildroot}/%{_datadir}/openquake/risklib
cp -R demos %{buildroot}/%{_datadir}/openquake/risklib

%clean
rm -rf %{buildroot}

%files -f INSTALLED_FILES
%defattr(-,root,root)
%doc LICENSE README.md doc
%dir %{_datadir}/openquake
%{_datadir}/openquake/risklib

%changelog
* %(date -d @%{oqtimestamp} '+%a %b %d %Y') GEM Automatic Packager <gem-autopack@openquake.org> %{oqversion}-%{oqtimestamp}_%{oqrelease}
– Unstable release of %{oqname}
