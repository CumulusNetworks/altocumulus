%define name altocumulus
%define version 0.1.0.dev21
%define unmangled_version 0.1.0.dev21
%define unmangled_version 0.1.0.dev21
%define release 1

Summary: UNKNOWN
Name: %{name}
Version: %{version}
Release: %{release}
Source0: %{name}-%{unmangled_version}.tar.gz
License: UNKNOWN
Group: Development/Libraries
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Prefix: %{_prefix}
BuildArch: noarch
Vendor: Ian Unruh <ianunruh@gmail.com>

%description
# Altocumulus

**IMPORTANT** This is in development and demo ready.

Integrate your Cumulus Linux switch with OpenStack Neutron

Manages VLAN bridges on the switch and L2 connectivity between (compute) hosts and the VLAN bridges. Uses LLDP to perform auto-discovery of hosts and the switchports they are connected to.

Uses the same conventions as the Linux Bridge agent so that DHCP/L3 agents can theoretically be hosted on the switch.

This branch includes changes conducted by Ceng to understand strengths and
weakness of plugin for future development and improvement.

## Usage

There are two components involved in this project:

* ML2 mechanism driver (runs on hosts with Neutron server)
* HTTP API server (runs on switches)

## Requirements
  Openstack Kilo Release. Does not work with Juno or Older releases
  LLDP must be active on all compute nodes and switches. Suggest enabling PTM a
valid topology.dot file in place to verify LLDP status

## Supported Topology
  Singly attached server to a switch, with single or bond L2 links between
switches.

## Sample Cumulus Linux Base Configuration

```
leaf1 | success | rc=0 >>
---------------------------
auto swp32s0
iface swp32s0
        alias connection to server2
auto bond0
iface bond0
        mstpctl-portnetwork yes
        bond-miimon 100
        bond-lacp-rate 1
        bond-min-links 1
        bond-slaves glob swp17-18
        bond-mode 802.3ad
        bond-xmit-hash-policy layer3+4
        mstpctl-bpduguard no
auto lo
iface lo inet loopback
auto eth0
iface eth0 inet dhcp


leaf2 | success | rc=0 >>
------------------------
auto swp32s0
iface swp32s0
        alias connection to server1
auto bond0
iface bond0
        mstpctl-portnetwork yes
        bond-miimon 100
        bond-lacp-rate 1
        bond-min-links 1
        bond-slaves glob swp17-18
        bond-mode 802.3ad
        bond-xmit-hash-policy layer3+4
        mstpctl-bpduguard no
auto lo
iface lo inet loopback
auto eth0
iface eth0 inet dhcp
```

## Installation

### ML2 mechanism driver

#### Redhat Openstack

```bash
# yum install git rpm-build
# ps -ef | grep neutron-server # confirm neutron server is running on this otherwise find the right server
#  git clone http://github.com/CumulusNetworks/altocumulus
# cd altocumulus
# python setup.py bdist_rpm
# rpm -ivh dist/altocumulus-0.1.0.dev13-1.noarch.rpm

```

2. Add `cumulus` to the `mechanism_drivers` field in `/etc/neutron/plugins/ml2/ml2_conf.ini`
3. _Append_ the sample ml2_cumulus_ini in this repo to  `/etc/neutron/plugins/ml2/ml2_conf.ini` on the network node.

### HTTP API server

A debian package can be build using information included in the debian directory

## TODO

* Authentication and Secure Communication (SSL)



%prep
%setup -n %{name}-%{unmangled_version} -n %{name}-%{unmangled_version}

%build
python setup.py build

%install
python setup.py install --single-version-externally-managed -O1 --root=$RPM_BUILD_ROOT --record=INSTALLED_FILES

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES
%defattr(-,root,root)
