# Altocumulus


Integrate your Cumulus Linux switch with OpenStack Neutron

Manages VLAN bridges on the switch and L2 connectivity between (compute) hosts and the VLAN bridges. Uses LLDP to perform auto-discovery of hosts and the switchports they are connected to.

Uses the same conventions as the Linux Bridge agent so that DHCP/L3 agents can theoretically be hosted on the switch.

The main branches in the repo, match Openstack Release names. 
Check out the release you need depending on your Openstack Version. Currently included is the
mechanism driver for `kilo` and `liberty`.

## Usage

There are two components involved in this project:

* ML2 mechanism driver (runs on hosts with Neutron server)
* HTTP API server (runs on switches)

## Installation

### ML2 mechanism driver

The easiest way so far to install the mechanism driver is to `git clone` the
project onto the network node and install it there using `python setup.py
install` Or create your own python wheel of the project using the `python
setup.py bdist_wheel` option.

2. Add `cumulus` to the `mechanism_drivers` field in
   `/etc/neutron/plugins/ml2/ml2_conf.ini`

3. Add the switches the mechanism driver needs to talk to in the
   `/etc/neutron/plugins/ml2/ml2_conf.ini` file.

```
[ml2_cumulus]
switches = leaf1,leaf2
```

### HTTP API server

1. Install debian wheezy backports
```
# /etc/apt/sources.list.d/backports.list
----
deb [arch=amd64] http://http.debian.net/debian wheezy main                                                     
deb [arch=amd64] http://http.debian.net/debian wheezy-backports main
```

2. Install flask, requests, python-six
```
sudo apt-get install -t wheezy-backports python-requests python-chardet
python-urllib3 python-six python-yaml python-flask

dpkg install altocumulus-driver deb.
sudo dpkg -i altocumulus-ml2-switch_0.1.0~dev28-2_all.deb
```

For cumulus 2.5 there is a debian package included in this project. Download and
install the deb using `dpkg -i`.

3. Modify the `/etc/altocumulus/config.yaml` to list the interswitch links.
   Example:
```
trunk_interfaces=bond0
```

### Restrictions

* Requires single attached servers.
* LLDP must be configured on the switches. Use Cumulus PTM to verify LLDP
  configuration
* Configure Switches in classic mode. Example:
```
auto swp32s0
iface swp32s0
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
> Note:
>This is demo ready version of the Cumulus ML2 Mechanism Driver. It
> **is not production ready**.

## To-do

* Authentication and secure connection between Openstack Neutron and Switch
* Manage State in case of unexpected events.
