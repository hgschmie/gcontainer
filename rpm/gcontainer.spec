# RPM build script must define _TAG_OR_SHA and _REVISION

Name:          gcontainer
Version:       %{_TAG_OR_SHA}
Release:       %{_REVISION}.%{?dist}
Summary:       G Container deployment tool
License:       BSD
Packager:      Henning Schmiedehausen <henning@example.com>
Vendor:        Henning
Distribution:  G
Source0:       gcontainer-%{_TAG_OR_SHA}.tar.gz
BuildRequires: python-virtualenv
BuildRequires: python-devel >= 2.7.5
BuildRequires: libffi-devel, openssl-devel
Requires:      docker >= 1.5.0

%description
G Container deployment tool.


%prep
%setup -n gcontainer-%{_TAG_OR_SHA}

%install
if [ -e %{buildroot}%{_libexecdir}/gcontainer -a "%{buildroot}" != '/' ]; then
  rm -rf %{buildroot}%{_libexecdir}/gcontainer
fi

install -d %{buildroot}%{_libexecdir}/gcontainer
virtualenv %{buildroot}%{_libexecdir}/gcontainer

export VIRTUAL_ENV=%{buildroot}%{_libexecdir}/gcontainer
export PATH="$VIRTUAL_ENV/bin:$PATH"
unset PYTHON_HOME
python setup.py clean build install
virtualenv --relocatable %{buildroot}%{_libexecdir}/gcontainer
find %{buildroot}%{_libexecdir}/gcontainer -name \*.pyc | xargs rm -f
find %{buildroot}%{_libexecdir}/gcontainer -type f -print0 | xargs -0 perl -pi -e "s|%{buildroot}||g"

rm -f %{buildroot}%{_libexecdir}/gcontainer/bin/python
ln -s %{_bindir}/python %{buildroot}%{_libexecdir}/gcontainer/bin/python

install -d %{buildroot}%{_bindir}
ln -s %{_libexecdir}/gcontainer/bin/gcontainer %{buildroot}%{_bindir}/gcontainer

%clean
exit 0


%files
%defattr(-, root, root)
%{_bindir}/gcontainer
%{_libexecdir}/gcontainer


%changelog
* Mon May 11 2015 Henning Schmiedehausen <henning@example.com> - 1.0-1
- first real release, 1.0

* Mon May 04 2015 Henning Schmiedehausen <henning@example.com> - 0.0.2-1
- bump to 0.0.2

* Wed Apr 29 2015 Henning Schmiedehausen <henning@example.com> - 0.0.1-2
- get dependencies right for building on CentOS 7.

* Mon Apr 27 2015 Henning Schmiedehausen <henning@example.com> - 0.0.1-1
- initial build
