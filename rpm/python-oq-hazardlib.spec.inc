%define oqstable ##_stable_##
%define oqrepo ##_repo_##
%define oqversion ##_version_##
%define oqrelease ##_release_##
%define oqname python-%{oqrepo}
%define oqtimestamp ##_timestamp_##

Summary: hazardlib is a library for performing seismic hazard analysis
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
Url: http://github.com/gem/oq-hazardlib

%define common_deps python numpy scipy python-shapely python-psutil h5py python-mock python-rtree
%define dev_deps python-nose python-coverage
Requires: %{common_deps}
Requires: %{dev_deps}

# Since tests are currently not enabled during the packaging phase, the following build dependencies are not required
#BuildRequires: %{common_deps}
#BuildRequires: %{dev_deps}

BuildRequires: gcc
BuildRequires: numpy
BuildRequires: python-devel
BuildRequires: python-setuptools

%description

hazardlib includes modules for modeling seismic sources (point, area and fault),
earthquake ruptures, temporal (e.g. Poissonian) and magnitude occurrence
models (e.g. Gutenberg-Richter), magnitude/area scaling relationships,
ground motion and intensity prediction equations (i.e. GMPEs and IPEs).
Eventually it will offer a number of calculators for hazard curves,
stochastic event sets, ground motion fields and disaggregation histograms.

hazardlib aims at becoming an open and comprehensive tool for seismic hazard
analysis. The GEM Foundation (http://www.globalquakemodel.org/) supports
the development of the  library by adding the most recent methodologies
adopted by the seismological/seismic hazard communities. Comments,
suggestions and criticisms from the community are always very welcome.

Copyright (C) 2014-2016 GEM Foundation


%prep
%if %{oqstable} == 1
%setup -n %{oqrepo}-%{oqversion} -n %{oqrepo}-%{oqversion}
%else
%setup -n %{oqrepo}-%{oqversion}-%{oqrelease} -n %{oqrepo}-%{oqversion}-%{oqrelease}
%endif

%build
env CFLAGS="$RPM_OPT_FLAGS" python setup.py build

%check
#nosetests -v -a '!slow' --with-doctest --with-coverage --cover-package=openquake.hazardlib

%install
sed -i "s/^__version__[  ]*=.*/__version__ = '%{oqversion}-%{oqrelease}'/g" openquake/hazardlib/__init__.py
python setup.py install --single-version-externally-managed -O1 --root=%{buildroot} --record=INSTALLED_FILES

%clean
rm -rf %{buildroot}

%files -f INSTALLED_FILES
%defattr(-,root,root)
%doc CONTRIBUTORS.txt LICENSE README.md doc

%changelog
%if %{oqstable} == 1
* %(date -d @%{oqtimestamp} '+%a %b %d %Y') GEM Automatic Packager <gem-autopack@openquake.org> %{oqversion}-%{oqrelease}
– Stable release of %{oqname}
%else
* %(date -d @%{oqtimestamp} '+%a %b %d %Y') GEM Automatic Packager <gem-autopack@openquake.org> %{oqversion}-%{oqtimestamp}_%{oqrelease}
– Unstable release of %{oqname}
%endif
