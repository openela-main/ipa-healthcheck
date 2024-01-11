%global project freeipa
%global shortname healthcheck
%global longname ipa%{shortname}
%global debug_package %{nil}
%global python3dir %{_builddir}/python3-%{name}-%{version}-%{release}
%{!?python3_sitelib: %global python3_sitelib %(%{__python3} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}


Name:           ipa-healthcheck
Version:        0.12
Release:        1%{?dist}
Summary:        Health check tool for IdM
BuildArch:      noarch
License:        GPLv3
URL:            https://github.com/%{project}/freeipa-healthcheck
Source0:        https://github.com/%{project}/%{name}/archive/%{version}.tar.gz#/%{version}.tar.gz
Source1:        %{longname}.conf

Patch0001:      0001-Remove-ipaclustercheck.patch
Patch0002:      0002-Disable-two-failing-tests.patch
Patch0003:      0003-Fix-logging-issue-related-to-dtype.patch

Requires:       %{name}-core = %{version}-%{release}
Requires:       ipa-server
Requires:       python3-ipalib
Requires:       python3-ipaserver
Requires:       python3-lib389
# cronie-anacron provides anacron
Requires:       anacron
Requires:       logrotate
Requires(post): systemd-units
Requires:       %{name}-core = %{version}-%{release}
BuildRequires:  python3-devel
BuildRequires:  systemd-devel
%{?systemd_requires}


%description
The FreeIPA health check tool provides a set of checks to
proactively detect defects in a FreeIPA cluster.

%package -n %{name}-core
Summary: Core plugin system for healthcheck
# No Requires on %%{name} = %%{version}-%%{release} since this can be
# installed standalone
Conflicts: %{name} < 0.4

%description -n %{name}-core
Core files


%prep
%autosetup -p1 -n %{project}-%{shortname}-%{version}


%build
%py3_build


%install
%py3_install

mkdir -p %{buildroot}%{_sysconfdir}/%{longname}
install -m644 %{SOURCE1} %{buildroot}%{_sysconfdir}/%{longname}

mkdir -p %{buildroot}/%{_unitdir}
install -p -m644 %{_builddir}/%{project}-%{shortname}-%{version}/systemd/ipa-%{shortname}.service %{buildroot}%{_unitdir}
install -p -m644 %{_builddir}/%{project}-%{shortname}-%{version}/systemd/ipa-%{shortname}.timer %{buildroot}%{_unitdir}

mkdir -p %{buildroot}/%{_libexecdir}/ipa
install -p -m755 %{_builddir}/%{project}-%{shortname}-%{version}/systemd/ipa-%{shortname}.sh %{buildroot}%{_libexecdir}/ipa/

mkdir -p %{buildroot}%{_sysconfdir}/logrotate.d
install -p -m644 %{_builddir}/%{project}-%{shortname}-%{version}/logrotate/%{longname} %{buildroot}%{_sysconfdir}/logrotate.d

mkdir -p %{buildroot}/%{_localstatedir}/log/ipa/%{shortname}

mkdir -p %{buildroot}/%{_mandir}/man8
mkdir -p %{buildroot}/%{_mandir}/man5
install -p -m644 %{_builddir}/%{project}-%{shortname}-%{version}/man/man8/ipa-%{shortname}.8  %{buildroot}%{_mandir}/man8/
install -p -m644 %{_builddir}/%{project}-%{shortname}-%{version}/man/man5/%{longname}.conf.5  %{buildroot}%{_mandir}/man5/

(cd %{buildroot}/%{python3_sitelib}/ipahealthcheck && find . -type f  | \
    grep -v '^./core' | \
    grep -v 'opt-1' | \
    sed -e 's,\.py.*$,.*,g' | sort -u | \
    sed -e 's,\./,%%{python3_sitelib}/ipahealthcheck/,g' ) >healthcheck.list

%post
%systemd_post ipa-%{shortname}.service


%preun
%systemd_preun ipa-%{shortname}.service


%postun
%systemd_postun_with_restart ipa-%{shortname}.service


%files -f healthcheck.list
%{!?_licensedir:%global license %%doc}
%license COPYING
%doc README.md
%{_bindir}/ipa-%{shortname}
%dir %{_sysconfdir}/%{longname}
%dir %{_localstatedir}/log/ipa/%{shortname}
%config(noreplace) %{_sysconfdir}/%{longname}/%{longname}.conf
%config(noreplace) %{_sysconfdir}/logrotate.d/%{longname}
%{python3_sitelib}/%{longname}-%{version}-*.egg-info/
%{python3_sitelib}/%{longname}-%{version}-*-nspkg.pth
%{_unitdir}/*
%{_libexecdir}/*
%{_mandir}/man8/*
%{_mandir}/man5/*

%files -n %{name}-core
%{!?_licensedir:%global license %%doc}
%license COPYING
%doc README.md
%{python3_sitelib}/%{longname}/core/


%changelog
* Thu Dec 01 2022 Rob Crittenden <rcritten@redhat.com> - 0.12-1
- Update to upstream 0.12 (#2139529)
- Verify that the number of krb5kdc worker processes is aligned to the
  number of configured CPUs (#2052930)
- IPADNSSystemRecordsCheck displays warning message for 2 expected
  ipa-ca AAAA records (#2099484)

* Wed May 25 2022 Rob Crittenden <rcritten@redhat.com> - 0.7-14
- Add CLI options to healthcheck configuration file (#1872467)

* Fri Apr 29 2022 Rob Crittenden <rcritten@redhat.com> - 0.7-13
- Allow multiple file modes in the FileChecker (#2058239)

* Thu Mar 31 2022 Rob Crittenden <rcritten@redhat.com> - 0.7-12
- Use the subject base from the IPA configuration, not REALM (#2066308)

* Fri Mar 18 2022 Rob Crittenden <rcritten@redhat.com> - 0.7-11
- Add support for the DNS URI type (#2037847)

* Thu Feb 17 2022 Rob Crittenden <rcritten@redhat.com> - 0.7-10
- Don't depend on IPA status when suppressing pki checks (#2055316)

* Mon Jan 17 2022 Rob Crittenden <rcritten@redhat.com> - 0.7-9
- Don't assume the entry_point order when determining if there is a
  CA installed (#2041995)

* Thu Jan 06 2022 Rob Crittenden <rcritten@redhat.com> - 0.7-8
- Suppress the CRLManager check false positive when a CA is not
  configured (#1983060)
- Fix the backport of the pki.server.healthcheck suppression (#1983060)

* Thu Oct 07 2021 Rob Crittenden <rcritten@redhat.com> - 0.7-7
- ipa-healthcheck command takes some extra time to complete when dirsrv
  instance is stopped (#1776687)
- ipa-healthcheck complains about pki.server.healthcheck errors even CA
  is not configured on the replica (#1983060)

* Mon Jun 14 2021 Rob Crittenden <rcritten@redhat.com> - 0.7-6
- Fix patch fuzz issues, apply add'l upstream for log files (#1780020)

* Wed Jun  2 2021 Rob Crittenden <rcritten@redhat.com> - 0.7-5
- Return a user-friendly message when no issues are found (#1780062)
- Report on FIPS status (#1781107)
- Detect mismatches beteween certificates in LDAP and filesystem (#1886770)
- Verify owner/perms for important log files (#1780020)

* Tue Apr  6 2021 Rob Crittenden <rcritten@redhat.com> - 0.7-4
- Add check to validate the KRA Agent is correct (#1894781)

* Fri Dec  4 2020 Rob Crittenden <rcritten@redhat.com> - 0.7-3
- Translate result names when reading input from a json file (#1866558)

* Tue Nov  3 2020 Rob Crittenden <rcritten@redhat.com> - 0.7-2
- Fix collection of AD trust domains (#1891505) 

* Tue Nov  3 2020 Rob Crittenden <rcritten@redhat.com> - 0.7-1
- Update to upstream 0.7 (#1891850)
- Include Directory Server healthchecks (#1824193)
- Document that default output format is JSON (#1780328)
- Fix return value on exit with --input-file (#1866558)
- Fix examples in man page (#1809215)
- Replace man page reference to output-format with output-type (#1780303)
- Add dependencies on services to avoid false positives (#1780510)

* Wed Aug 19 2020 Rob Crittenden <rcritten@redhat.com> - 0.4-6
- The core subpackage can be installed standalone, drop the Requires
  on the base package. (#1852244)
- Add Conflicts < 0.4 to to core to allow downgrading with
  --allowerasing (#1852244)

* Tue Aug  4 2020 Rob Crittenden <rcritten@redhat.com> - 0.4-5
- Remove the Obsoletes < 0.4 and add same-version Requires to each
  subpackage so that upgrades from 0.3 will work (#1852244)

* Thu Jan 16 2020 Rob Crittenden <rcritten@redhat.com> - 0.4-4
- Allow plugins to read contents from config during initialization (#1784037)

* Thu Dec  5 2019 Rob Crittenden <rcritten@redhat.com> - 0.4-3
- Add Obsoletes to core subpackage (#1780121)

* Mon Dec  2 2019 Rob Crittenden <rcritten@redhat.com> - 0.4-2
- Abstract processing so core package is standalone (#1771710)

* Mon Dec  2 2019 Rob Crittenden <rcritten@redhat.com> - 0.4-1
- Rebase to upstream 0.4 (#1770346)
- Create subpackage to split out core processing (#1771710)
- Correct URL (#1773512)
- Errors not translated to strings (#1752849)
- JSON output not indented by default (#1729043)
- Add dependencies to checks to avoid false-positives (#1727900)
- Verify expected DNS records (#1695125)

* Mon Aug 12 2019 Rob Crittenden <rcritten@redhat.com> - 0.3-4
- Lookup AD user by SID and not by hardcoded username (#1739500)

* Thu Aug  8 2019 Rob Crittenden <rcritten@redhat.com> - 0.3-3
- The AD trust agent and controller are not being initialized (#1738314)

* Mon Aug  5 2019 Rob Crittenden <rcritten@redhat.com> - 0.3-2
- Change DNA plugin to return WARNING if no range is set (#1737492)

* Mon Jul 29 2019 François Cami <fcami@redhat.com> - 0.3-1
- Update to upstream 0.3 (#1701351)
- Add logrotate configs + depend on anacron and logrotate (#1729207)

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
