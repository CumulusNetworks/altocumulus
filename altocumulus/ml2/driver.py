import json

from oslo.config import cfg
import requests
from requests.exceptions import HTTPError

from neutron.extensions import portbindings
from neutron.plugins.ml2.common.exceptions import MechanismDriverError
from neutron.plugins.ml2.driver_api import MechanismDriver

from altocumulus.ml2 import config

NETWORKS_URL = '{base}/networks/{network}'
HOSTS_URL = '{base}/networks/{network}/hosts/{host}'

class CumulusMechanismDriver(MechanismDriver):
    """
    Mechanism driver for Cumulus Linux that manages connectivity between switches
    and (compute) hosts using the Altocumulus API

    Inspired by the Arista ML2 mechanism driver
    """
    def initialize(self):
        self.url = cfg.CONF.ml2_cumulus.url

    def create_network_postcommit(self, context):
        network_id = context.current['id']
        vlan_id = context.network_segments[0].segmentation_id

        request = {
            'vlan': vlan_id,
        }

        r = requests.put(
            NETWORKS_URL.format(base=self.url, network=network_id),
            data=json.dumps(request))

        if r.status_code != requests.codes.ok:
            raise MechanismDriverError()

    def delete_network_postcommit(self, context):
        network_id = context.current['id']

        r = requests.delete(
            NETWORKS_URL.format(base=self.url, network=network_id))

        if r.status_code != requests.codes.ok:
            raise MechanismDriverError()

    def create_port_postcommit(self, context):
        port = context.current

        device_id = port['device_id']
        device_owner = port['device_owner']
        host = port[portbindings.HOST_ID]
        network_id = port['network_id']

        if not (host and device_id and device_owner):
            return

        r = requests.put(
            HOSTS_URL.format(base=self.url, network=network_id, host=host))

        if r.status_code != requests.codes.ok:
            raise MechanismDriverError()

    def delete_port_postcommit(self, context):
        port = context.current

        host = port[portbindings.HOST_ID]
        network_id = port['network_id']

        r = requests.delete(
            HOSTS_URL.format(base=self.url, network=network_id, host=host))

        if r.status_code != requests.codes.ok:
            raise MechanismDriverError()
