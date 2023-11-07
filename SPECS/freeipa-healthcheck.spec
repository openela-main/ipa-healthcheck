%if 0%{?rhel}
%global prefix ipa
%global productname IPA
%global alt_prefix freeipa
%else
# Fedora
%global prefix freeipa
%global productname FreeIPA
%global alt_prefix ipa
%endif
%global debug_package %{nil}
%global python3dir %{_builddir}/python3-%{name}-%{version}-%{release}
%{!?python3_sitelib: %global python3_sitelib %(%{__python3} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}
%global alt_name %{alt_prefix}-healthcheck

%bcond_without tests

Name:           %{prefix}-healthcheck
Version:        0.12
Release:        4%{?dist}
Summary:        Health check tool for %{productname}
BuildArch:      noarch
License:        GPLv3
URL:            https://github.com/freeipa/freeipa-healthcheck
Source0:        https://github.com/freeipa/freeipa-healthcheck/archive/%{version}.tar.gz
Source1:        ipahealthcheck.conf

Patch0001:      0001-Remove-ipaclustercheck.patch
Patch0002:      0002-Disable-two-failing-tests.patch
Patch0003:      0003-Skip-AD-domains-with-posix-ranges-in-the-catalog-che.patch
Patch0004:      0004-Catch-exceptions-during-user-group-name-lookup-in-Fi.patch
Patch0005:      0005-Don-t-error-in-DogtagCertsConnectivityCheck-with-ext.patch

Requires:       %{name}-core = %{version}-%{release}
Requires:       %{prefix}-server
Requires:       python3-ipalib
Requires:       python3-ipaserver
Requires:       python3-lib389 >= 1.4.2.14-1
# cronie-anacron provides anacron
Requires:       anacron
Requires:       logrotate
Requires(post): systemd-units
Requires:       %{name}-core = %{version}-%{release}
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  systemd-devel
%{?systemd_requires}
# packages for make check
%if %{with tests}
BuildRequires:  python3-pytest
BuildRequires:  python3-ipalib
BuildRequires:  python3-ipaserver
%endif
BuildRequires:  python3-lib389
BuildRequires:  python3-libsss_nss_idmap

# Cross-provides for sibling OS
Provides:       %{alt_name} = %{version}
Conflicts:      %{alt_name}
Obsoletes:      %{alt_name} < %{version}

%description
The %{productname} health check tool provides a set of checks to
proactively detect defects in a FreeIPA cluster.


%package -n %{name}-core
Summary: Core plugin system for healthcheck

# Cross-provides for sibling OS
Provides:       %{alt_name}-core = %{version}
Conflicts:      %{alt_name}-core
Obsoletes:      %{alt_name}-core < %{version}


%description -n %{name}-core
Core plugin system for healthcheck, usable standalone with other
packages.


%prep
%autosetup -p1  -n freeipa-healthcheck-%{version}


%build
%py3_build


%install
%py3_install

mkdir -p %{buildroot}%{_sysconfdir}/ipahealthcheck
install -m644 %{SOURCE1} %{buildroot}%{_sysconfdir}/ipahealthcheck

mkdir -p %{buildroot}/%{_unitdir}
install -p -m644 %{_builddir}/freeipa-healthcheck-%{version}/systemd/ipa-healthcheck.service %{buildroot}%{_unitdir}
install -p -m644 %{_builddir}/freeipa-healthcheck-%{version}/systemd/ipa-healthcheck.timer %{buildroot}%{_unitdir}

mkdir -p %{buildroot}/%{_libexecdir}/ipa
install -p -m755 %{_builddir}/freeipa-healthcheck-%{version}/systemd/ipa-healthcheck.sh %{buildroot}%{_libexecdir}/ipa/

mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d
install -p -m644 %{_builddir}/freeipa-healthcheck-%{version}/logrotate/ipahealthcheck %{buildroot}%{_sysconfdir}/logrotate.d

mkdir -p %{buildroot}/%{_localstatedir}/log/ipa/healthcheck

mkdir -p %{buildroot}/%{_mandir}/man8
mkdir -p %{buildroot}/%{_mandir}/man5
install -p -m644 %{_builddir}/freeipa-healthcheck-%{version}/man/man8/ipa-healthcheck.8  %{buildroot}%{_mandir}/man8/
install -p -m644 %{_builddir}/freeipa-healthcheck-%{version}/man/man5/ipahealthcheck.conf.5  %{buildroot}%{_mandir}/man5/

(cd %{buildroot}/%{python3_sitelib}/ipahealthcheck && find . -type f  | \
    grep -v '^./core' | \
    grep -v 'opt-1' | \
    sed -e 's,\.py.*$,.*,g' | sort -u | \
    sed -e 's,\./,%%{python3_sitelib}/ipahealthcheck/,g' ) >healthcheck.list


%if %{with tests}
%check
PYTHONPATH=src PATH=$PATH:$RPM_BUILD_ROOT/usr/bin pytest-3 tests/test_*
%endif


%post
%systemd_post ipa-healthcheck.service


%preun
%systemd_preun ipa-healthcheck.service


%postun
%systemd_postun_with_restart ipa-healthcheck.service


%files -f healthcheck.list
%{!?_licensedir:%global license %%doc}
%license COPYING
%doc README.md
%{_bindir}/ipa-healthcheck
%dir %{_sysconfdir}/ipahealthcheck
%dir %{_localstatedir}/log/ipa/healthcheck
%config(noreplace) %{_sysconfdir}/ipahealthcheck/ipahealthcheck.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/ipahealthcheck
%{python3_sitelib}/ipahealthcheck-%{version}-*.egg-info/
%{python3_sitelib}/ipahealthcheck-%{version}-*-nspkg.pth
%{_unitdir}/*
%{_libexecdir}/*
%{_mandir}/man8/*
%{_mandir}/man5/*


%files -n %{name}-core
%{!?_licensedir:%global license %%doc}
%license COPYING
%doc README.md
%{python3_sitelib}/ipahealthcheck/core/


%changelog
* Mon Jul 24 2023 Rob Crittenden <rcritten@redhat.com> - 0.12-4
- Error in DogtagCertsConnectivityCheckCA with external CA (#2224595)

* Thu Jul 06 2023 Rob Crittenden <rcritten@redhat.com> - 0.12-3
- Catch exceptions during user/group name lookup in FileCheck (#2218912)

* Tue Apr 25 2023 Rob Crittenden <rcritten@redhat.com> - 0.12-2
- Skip AD domains with posix ranges in the catalog check (#2188135)

* Thu Dec 01 2022 Rob Crittenden <rcritten@redhat.com> - 0.12-1
- Update to upstream 0.12 (#2139531)

* Wed Jul 06 2022 Rob Crittenden <rcritten@redhat.com> - 0.9-9
- Add support for the DNS URI type (#2104495)

* Wed May 18 2022 Rob Crittenden <rcritten@redhat.com> - 0.9-8
- Validate that a known output type has been selected (#2079698)

* Wed May 04 2022 Rob Crittenden <rcritten@redhat.com> - 0.9-7
- debug='True' in ipahealthcheck.conf doesn't enable debug output (#2079861)
- Validate value formats in the ipahealthcheck.conf file (#2079739)
- Validate output_type options from ipahealthcheck.conf file (#2079698)

* Thu Apr 28 2022 Rob Crittenden <rcritten@redhat.com> - 0.9-6
- Allow multiple file modes in the FileChecker (#2072708)

* Wed Apr 06 2022 Rob Crittenden <rcritten@redhat.com> - 0.9-5
- Add CLI options to healthcheck configuration file (#2070981)

* Wed Mar 30 2022 Rob Crittenden <rcritten@redhat.com> - 0.9-4
- Use the subject base from the IPA configuration, not REALM (#2067213) 

* Tue Oct 12 2021 Rob Crittenden <rcritten@redhat.com> - 0.9-3
- IPATrustControllerServiceCheck doesn't handle HIDDEN_SERVICE (#1976878)

* Mon Aug 09 2021 Mohan Boddu <mboddu@redhat.com> - 0.9-2
- Rebuilt for IMA sigs, glibc 2.34, aarch64 flags
  Related: rhbz#1991688

* Thu Jun 17 2021 Rob Crittenden <rcritten@redhat.com> - 0.9-1
- Rebase to upstream 0.9 (#1969539)

* Thu Apr 22 2021 Rob Crittenden <rcritten@redhat.com> - 0.8-7.2
- rpminspect: specname match on suffix to allow for differing
  spec/package naming (#1951733)

* Mon Apr 19 2021 Rob Crittenden <rcritten@redhat.com> - 0.8-7.1
- Switch from tox to pytest as the test runner. tox is being deprecated
  in some distros. (#1942157)

* Mon Apr 19 2021 Rob Crittenden <rcritten@redhat.com> - 0.8-7
- Add check to validate the KRA Agent is correct (#1894781)

* Thu Apr 15 2021 Mohan Boddu <mboddu@redhat.com> - 0.8-6.1
- Rebuilt for RHEL 9 BETA on Apr 15th 2021. Related: rhbz#1947937

* Fri Mar 12 2021 Alexander Bokovoy <abokovoy@redhat.com> - 0.8-5.1
- Re-enable package self-tests after bootstrap

* Mon Mar  8 2021 François Cami <fcami@redhat.com> - 0.8-5
- Make the spec file distribution-agnostic (rhbz#1935773).

* Tue Mar  2 2021 Alexander Scheel <ascheel@redhat.com> - 0.8-4
- Make the spec file more distribution-agnostic
- Use tox as the test runner when tests are enabled

* Tue Jan 26 2021 Fedora Release Engineering <releng@fedoraproject.org> - 0.8-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_34_Mass_Rebuild

* Mon Jan 18 2021 Rob Crittenden <rcritten@redhat.com> - 0.8-2
- A bad file group was reported as a python list, not a string

* Wed Jan 13 2021 Rob Crittenden <rcritten@redhat.com> - 0.8-1
- Update to upstream 0.8
- Fix FTBFS in F34/rawhide (#1915256)

* Wed Dec 16 2020 Rob Crittenden <rcritten@redhat.com> - 0.7-3
- Include upstream patch to fix parsing input from json files

* Tue Nov 17 2020 Rob Crittenden <rcritten@redhat.com> - 0.7-2
- Include upstream patch to fix collection of AD trust domains
- Include upstream patch to fix failing not-valid-after test

* Thu Oct 29 2020 Rob Crittenden <rcritten@redhat.com> - 0.7-1
- Update to upstream 0.7

* Wed Jul 29 2020 Rob Crittenden <rcritten@redhat.com> - 0.6-4
- Set minimum Requires on python3-lib389
- Don't assume that all users of healthcheck-core provide the same
  set of options.

* Mon Jul 27 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.6-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_33_Mass_Rebuild

* Fri Jul 24 2020 Rob Crittenden <rcritten@redhat.com> - 0.6-2
- Don't collect IPA servers in MetaCheck
- Skip if dirsrv not available in IPAMetaCheck

* Wed Jul  1 2020 Rob Crittenden <rcritten@redhat.com> - 0.6-1
- Update to upstream 0.6
- Don't include cluster checking yet

* Tue Jun 23 2020 Rob Crittenden <rcritten@redhat.com> - 0.5-5
- Add BuildRequires on python3-setuptools

* Tue May 26 2020 Miro Hrončok <mhroncok@redhat.com> - 0.5-4
- Rebuilt for Python 3.9

* Tue Jan 28 2020 Fedora Release Engineering <releng@fedoraproject.org> - 0.5-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_32_Mass_Rebuild

* Mon Jan 27 2020 Rob Crittenden <rcritten@redhat.com> - 0.5-2
- Rebuild

* Thu Jan  2 2020 Rob Crittenden <rcritten@redhat.com> - 0.5-1
- Update to upstream 0.5

* Mon Dec 2 2019 François Cami <fcami@redhat.com> - 0.4-2
- Create subpackage to split out core processing (#1771710)

* Mon Dec 2 2019 François Cami <fcami@redhat.com> - 0.4-1
- Update to upstream 0.4
- Change Source0 to something "spectool -g" can use. 
- Correct URL (#1773512)
- Errors not translated to strings (#1752849)
- JSON output not indented by default (#1729043)
- Add dependencies to checks to avoid false-positives (#1727900)
- Verify expected DNS records (#1695125

* Thu Oct 03 2019 Miro Hrončok <mhroncok@redhat.com> - 0.3-3
- Rebuilt for Python 3.8.0rc1 (#1748018)

* Mon Aug 19 2019 Miro Hrončok <mhroncok@redhat.com> - 0.3-2
- Rebuilt for Python 3.8

* Thu Jul 25 2019 François Cami <fcami@redhat.com> - 0.3-1
- Update to upstream 0.3
- Add logrotate configs + depend on anacron and logrotate

* Thu Jul 25 2019 François Cami <fcami@redhat.com> - 0.2-6
- Fix permissions

* Thu Jul 25 2019 Fedora Release Engineering <releng@fedoraproject.org> - 0.2-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Thu Jul 11 2019 François Cami <fcami@redhat.com> - 0.2-4
- Fix ipa-healthcheck.sh installation path (rhbz#1729188)
- Create and own log directory (rhbz#1729188)

* Tue Apr 30 2019 François Cami <fcami@redhat.com> - 0.2-3
- Add python3-lib389 to BRs

* Tue Apr 30 2019 François Cami <fcami@redhat.com> - 0.2-2
- Fix changelog

* Thu Apr 25 2019 Rob Crittenden <rcritten@redhat.com> - 0.2-1
- Update to upstream 0.2

* Thu Apr 4 2019 François Cami <fcami@redhat.com> - 0.1-2
- Explicitly list dependencies

* Tue Apr 2 2019 François Cami <fcami@redhat.com> - 0.1-1
- Initial package import
