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

The rpm directory to build a rpm package can be built to build the
``altocumulus-ml2-driver`` package

#### Debian based Systems

The debian directory to build a debian package can be built to build the
``altocumulus-ml2-driver`` package


#### Configuration on the network node

* Add `cumulus` to the `mechanism_drivers` field in `/etc/neutron/plugins/ml2/ml2_conf.ini`
* _Append_ the sample ml2_cumulus_ini in this repo to  `/etc/neutron/plugins/ml2/ml2_conf.ini` on the network node.

### HTTP API server

The debian directory to build a debian package can be built to build the
``altocumulus-ml2-switch` package

## TODO

* Authentication and Secure Communication (SSL) between the Cumulus Switch and
  Neutron server
