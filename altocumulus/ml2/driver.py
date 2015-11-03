import json

from oslo_config import cfg
from oslo_log import log as logging
import requests
from requests.exceptions import HTTPError

from neutron.extensions import portbindings
from neutron.i18n import _LE, _LI, _LW
from neutron.plugins.ml2.common.exceptions import MechanismDriverError
from neutron.plugins.ml2.driver_api import MechanismDriver

from altocumulus.ml2 import config

LOG = logging.getLogger(__name__)
NETWORKS_URL = '{scheme}://{base}:{port}/networks/{network}'
HOSTS_URL = '{scheme}://{base}:{port}/networks/{network}/hosts/{host}'
VXLAN_URL = '{scheme}://{base}:{port}/networks/{network}/vxlan/{vni}'
LINUXBRIDGE_AGENT = 'Linux bridge agent'


class CumulusMechanismDriver(MechanismDriver):
    """
    Mechanism driver for Cumulus Linux that manages connectivity between switches
    and (compute) hosts using the Altocumulus API

    Inspired by the Arista ML2 mechanism driver
    """
    def initialize(self):
        self.scheme = cfg.CONF.ml2_cumulus.scheme
        self.protocol_port = cfg.CONF.ml2_cumulus.protocol_port

    def bind_port(self, context):
        if context.binding_levels:
            return  # we've already got a top binding

        # assign a dynamic vlan
        next_segment = context.allocate_dynamic_segment(
            {'id': context.network.current, 'network_type': 'vlan'}
        )


        context.continue_binding(
            context.segments_to_bind[0]['id'],
            [next_segment]
        )

    def delete_network_postcommit(self, context):
        network_id = context.current['id']
        vni = context.current['provider:segmentation_id']

        agents = context._plugin.get_agents(
            context._plugin_context,
            filters={'agent_type': [LINUXBRIDGE_AGENT]}
        )


        # remove vxlan from all hosts - a little unpleasant
        for agent in agents:
            try:
                switch_mgmt_ip = agent['configurations']['switch_mgmt_ip']
                actions = [
                    VXLAN_URL.format(
                        scheme=self.scheme,
                        base=switch_mgmt_ip,
                        port=self.protocol_port,
                        vni=vni
                    ),
                    NETWORKS_URL.format(
                        scheme=self.scheme,
                        base=switch_mgmt_ip,
                        port=self.protocol_port,
                        network=network_id
                    )
                ]

                for action in actions:
                    r = requests.delete(action)

                    if r.status_code != requests.codes.ok:
                        LOG.info(
                            _LI('Error during %s delete. HTTP Error:%s'),
                            action, r.status_code
                        )

            except Exception, e:
                # errors might be normal, but should improve this
                LOG.info(_LI('Error during net delete. Error %s'), e)

    def create_port_postcommit(self, context):
        if context.segments_to_bind:
            self._add_to_switch(context)

    def update_port_postcommit(self, context):
        if context.host != context.original_host:
            self._remove_from_switch(context.original)
        self._add_to_switch(context)

    def delete_port_postcommit(self, context):
        self._remove_from_switch(context)

    def _add_to_switch(self, context):
        port = context.current

        device_id = port['device_id']
        device_owner = port['device_owner']
        host = port[portbindings.HOST_ID]
        network_id = port['network_id']
        vni = context.top_bound_segment['segmentation_id']
        vlan = context.bottom_bound_segment['segmentation_id']

        if not (host and device_id and device_owner):
            return

        agent = context.host_agents(LINUXBRIDGE_AGENT)

        if not agent:
            raise MechanismDriverError()

        switch_mgmt_ip = agent[0]['configurations']['switch_mgmt_ip']

        r = requests.put(
            NETWORKS_URL.format(
                scheme=self.scheme,
                base=switch_mgmt_ip,
                port=self.protocol_port,
                network=network_id
            ),
            data=json.dumps({'vlan': vlan})
        )

        if r.status_code != requests.codes.ok:
            raise MechanismDriverError()

        actions = [
            HOSTS_URL.format(
                scheme=self.scheme,
                base=switch_mgmt_ip,
                port=self.protocol_port,
                network=network_id,
                host=host
            ),
            VXLAN_URL.format(
                scheme=self.scheme,
                base=switch_mgmt_ip,
                port=self.protocol_port,
                network=network_id,
                vni=vni
            )
        ]

        for action in actions:
            r = requests.put(action)

            if r.status_code != requests.codes.ok:
                raise MechanismDriverError()

    def _remove_from_switch(self, context):
        port = context.current
        host = port[portbindings.HOST_ID]
        network_id = port['network_id']

        agent = context.host_agents(LINUXBRIDGE_AGENT)

        if not agent:
            raise MechanismDriverError()


        switch_mgmt_ip = agent[0]['configurations']['switch_mgmt_ip']

        r = requests.delete(
            HOSTS_URL.format(
                scheme=self.scheme,
                base=switch_mgmt_ip,
                port=self.protocol_port,
                network=network_id,
                host=host
            )
        )

        if r.status_code != requests.codes.ok:
            LOG.info(
                _LI('error (%d) deleting port for %s on switch: %s'),
                r.status_code,
                host,
                switch_mgmt_ip
            )
