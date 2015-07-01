%define repo ##_repo_##
%define version ##_version_##
%define release ##_release_##
%define name python-%{repo}

Summary: hazardlib is a library for performing seismic hazard analysis
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{repo}-%{version}-%{release}.tar.gz
License: AGPL3
Group: Applications/Engineering
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
Vendor: The GEM OpenQuake team <devops@openquake.org>
Url: http://github.com/gem/oq-hazardlib

BuildRequires: gcc

Requires: numpy
Requires: scipy
Requires: python-lxml
Requires: python-shapely
Requires: python-setuptools
Requires: python-mock

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

Copyright (C) 2012-2015, GEM Foundation.


%prep
%setup -n %{repo}-%{version}-%{release} -n %{repo}-%{version}-%{release}

%build
env CFLAGS="$RPM_OPT_FLAGS" python setup.py build

%install
python setup.py install --single-version-externally-managed -O1 --root=%{buildroot} --record=INSTALLED_FILES

%clean
rm -rf %{buildroot}

%files -f INSTALLED_FILES
%defattr(-,root,root)
%doc CONTRIBUTORS.txt LICENSE README.rst doc
