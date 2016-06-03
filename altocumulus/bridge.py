# Copyright 2015 Cumulus Networks, Inc
# Copyright 2012 Cisco Systems, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
#
# Performs per host Linux Bridge configuration for Neutron.
# Based on the structure of the OpenVSwitch agent in the
# Neutron OpenVSwitch Plugin.
# @author: Sumit Naiksatam, Cisco Systems, Inc.
import os
from subprocess import CalledProcessError

BRIDGE_NAME_PREFIX = 'br'
VXLAN_NAME_PREFIX = 'vxlan'

BRIDGE_INTERFACES_FS = '/sys/devices/virtual/net/{}/brif/'
SUBINTERFACE_NAME = '{}.{}'

#XXX This whole thing should just generate ifupdown2 config file fragment(s)
#    in /etc/network/interfaces.d (or possibly /tmp/interfaces.d) with their
#    own "ml2" allow class.  Then ifreload the "ml2" class.  That way we
#    don't need to write any sync code here for timer-based resyncs.
class LinuxBridgeManager(object):
    """
    Much of this code is from the Linux Bridge agent for Neutron
    """
    def __init__(self, shell):
        self.shell = shell

    def _device_exists(self, device):
        try:
            self.shell.call(['ip', 'link', 'show', 'dev', device])
        except CalledProcessError:
            return False
        return True

    def _interface_exists_on_bridge(self, bridge, interface):
        directory = BRIDGE_INTERFACES_FS.format(bridge)
        for filename in os.listdir(directory):
            if filename == interface:
                return True
        return False

    def _up_interface(self, interface):
        self.shell.call(['ip', 'link', 'set', interface, 'up'])

    def _down_interface(self, interface):
        self.shell.call(['ip', 'link', 'set', interface, 'down'])

    def _delete_interface(self, interface):
        if not self._device_exists(interface):
            return

        self._down_interface(interface)
        self.shell.call(['ip', 'link', 'delete', interface])


    def set_vxlan_opts(self, local_bind_ip, service_node_ip):
        #XXX Make DNS names work for these.
        self._local_bind_ip = local_bind_ip
        self._service_node_ip = service_node_ip

    def get_bridge_name(self, network_id):
        bridge_name = BRIDGE_NAME_PREFIX + network_id[0:12]
        return bridge_name

    def get_subinterface_name(self, physical_interface, vlan_id):
        return SUBINTERFACE_NAME.format(physical_interface, vlan_id)

    def get_vxlan_name(self, vni):
        return VXLAN_NAME_PREFIX + str(vni)

    def ensure_vlan(self, physical_interface, vlan_id):
        interface = self.get_subinterface_name(physical_interface, vlan_id)

        if not self._device_exists(interface):
            self.shell.call(['ip', 'link', 'add', 'link', physical_interface,
                             'name', interface, 'type', 'vlan', 'id', vlan_id])
            self._up_interface(interface)

        return interface

    def delete_vlan(self, physical_interface, vlan_id):
        interface = self.get_subinterface_name(physical_interface, vlan_id)
        self._delete_interface(interface)

    def ensure_vxlan(self, vni):
        interface = self.get_vxlan_name(vni)

        if not self._device_exists(interface):
            self.shell.call(['ip', 'link', 'add', interface, 'type', 'vxlan',
                             'id', vni, 'local', self._local_bind_ip,
                             'svcnode', self._service_node_ip])
            self._up_interface(interface)

        return interface

    def delete_vxlan(self, vni):
        interface = self.get_vxlan_name(vni)
        self._delete_interface(interface)

    def add_interface(self, bridge_name, interface_name):
        if self._interface_exists_on_bridge(bridge_name, interface_name):
            return

        self.shell.call(['brctl', 'addif', bridge_name, interface_name])

    def ensure_bridge(self, bridge_name):
        if self._device_exists(bridge_name):
            return

        self.shell.call(['brctl', 'addbr', bridge_name])
        self.shell.call(['brctl', 'stp', bridge_name, 'off'])
        self._up_interface(bridge_name)

    def remove_bridge(self, bridge_name):
        if not self._device_exists(bridge_name):
            return

        self._down_interface(bridge_name)
        self.shell.call(['brctl', 'delbr', bridge_name])
