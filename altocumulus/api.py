# Copyright 2015 Cumulus Networks, Inc

from argparse import ArgumentParser

from flask import Flask, Response, request

from altocumulus import utils
from altocumulus.bridge import LinuxBridgeManager
from altocumulus.discovery import DiscoveryManager
from altocumulus.utils import Shell

DEFAULT_API_BIND = '0.0.0.0'
DEFAULT_API_PORT = 8140
DEFAULT_ROOT_HELPER = 'sudo'

# TODO These should be persistent
networks = {
}
physical_interfaces = {
}
trunks = []

shell = Shell(DEFAULT_ROOT_HELPER)

lbm = LinuxBridgeManager(shell)
dm = DiscoveryManager(shell)

app = Flask(__name__)

def empty_response(status=200):
    return Response(None, status=200, mimetype='text/plain')

@app.route('/networks/<network_id>', methods=['PUT'])
def update_network(network_id):
    params = request.get_json(force=True)

    networks[network_id] = vlan_id = str(params['vlan'])

    bridge_name = lbm.get_bridge_name(network_id)
    lbm.ensure_bridge(bridge_name)

    for trunk in trunks:
        trunk_subinterface_name = lbm.ensure_vlan(trunk, vlan_id)
        lbm.add_interface(bridge_name, trunk_subinterface_name)

    return empty_response()

@app.route('/networks/<network_id>', methods=['DELETE'])
def delete_network(network_id):
    if network_id in networks:
        bridge_name = lbm.get_bridge_name(network_id)
        vlan_id = networks[network_id]

        for trunk in trunks:
            lbm.delete_vlan(trunk, vlan_id)

        lbm.remove_bridge(bridge_name)

        del networks[network_id]

    return empty_response()

@app.route('/networks/<network_id>/hosts/<host>', methods=['PUT'])
def plug_host_into_network(network_id, host):
    physical_interface = dm.find_interface(host)
    if not physical_interface:
        return empty_response()

    physical_interfaces[host] = physical_interface
    vlan_id = networks[network_id]

    bridge_name = lbm.get_bridge_name(network_id)
    subinterface_name = lbm.ensure_vlan(physical_interface, vlan_id)

    lbm.add_interface(bridge_name, subinterface_name)

    return empty_response()

@app.route('/networks/<network_id>/hosts/<host>', methods=['DELETE'])
def unplug_host_from_network(network_id, host):
    physical_interface = physical_interfaces.get(host)
    if not physical_interface:
        return empty_response()

    vlan_id = networks[network_id]

    lbm.delete_vlan(physical_interface, vlan_id)

    return empty_response()

@app.route('/networks/<network_id>/vxlan/<vni>', methods=['PUT'])
def plug_vxlan_into_network(network_id, vni):
    bridge_name = lbm.get_bridge_name(network_id)
    interface_name = lbm.ensure_vxlan(vni)

    lbm.add_interface(bridge_name, interface_name)

    return empty_response()

@app.route('/networks/<network_id>/vxlan/<vni>', methods=['DELETE'])
def unplug_vxlan_from_network(network_id, vni):
    vlan_id = networks[network_id]

    lbm.delete_vxlan(physical_interface, vlan_id)

    return empty_response()

def main():
    parser = ArgumentParser()
    parser.add_argument('-c', '--config-file', default='config.yaml')
    parser.add_argument('-d', '--debug', action='store_true')

    args = parser.parse_args()

    config = utils.load_config(args.config_file)

    bind = config.get('bind', DEFAULT_API_BIND)
    port = config.get('port', DEFAULT_API_PORT)

    trunks.extend(filter(len, config.get('trunk_interfaces', '').split(',')))

    lbm.set_vxlan_opts(config.get('local_bind', ''),
                       config.get('service_node', ''))

    app.debug = config.get('debug', False)
    app.run(host=bind, port=port)
