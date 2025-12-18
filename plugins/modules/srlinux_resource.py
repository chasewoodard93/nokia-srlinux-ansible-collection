#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Chase Woodard <chasewoodard93@users.noreply.github.com>
# MIT License

DOCUMENTATION = r'''
---
module: srlinux_resource
short_description: Manage specific SR Linux resources with CRUD operations
description:
  - This module provides resource-specific CRUD operations for Nokia SR Linux
  - Supports create, read, update, and delete operations on specific resources
  - Provides idempotent resource management
  - Works with interfaces, network-instances, BGP neighbors, and more
version_added: "1.3.0"
author:
  - Chase Woodard (@chasewoodard93)
options:
  resource_type:
    description:
      - Type of resource to manage
    required: true
    type: str
    choices:
      - interface
      - subinterface
      - network_instance
      - bgp_neighbor
      - bgp_group
      - static_route
      - acl
      - routing_policy
      - user
  name:
    description:
      - Name or identifier of the resource
    required: true
    type: str
  state:
    description:
      - Desired state of the resource
    required: false
    type: str
    choices: [present, absent]
    default: present
  config:
    description:
      - Configuration dictionary for the resource
      - Keys depend on the resource_type
    required: false
    type: dict
    default: {}
  network_instance:
    description:
      - Network instance context (for resources that require it)
    required: false
    type: str
    default: default
  host:
    description:
      - Hostname or IP address of the SR Linux device
    required: true
    type: str
  port:
    description:
      - SSH port number
    required: false
    type: int
    default: 22
  username:
    description:
      - Username for SSH authentication
    required: false
    type: str
    default: admin
  password:
    description:
      - Password for SSH authentication
    required: true
    type: str
  timeout:
    description:
      - Connection timeout in seconds
    required: false
    type: int
    default: 30
'''

EXAMPLES = r'''
- name: Create an interface
  chasewoodard93.srlinux.srlinux_resource:
    host: 172.20.20.101
    username: admin
    password: NokiaSrl1!
    resource_type: interface
    name: ethernet-1/1
    state: present
    config:
      admin_state: enable
      description: "Uplink to spine"
      mtu: 9214

- name: Create a BGP neighbor
  chasewoodard93.srlinux.srlinux_resource:
    host: "{{ ansible_host }}"
    username: "{{ ansible_user }}"
    password: "{{ ansible_password }}"
    resource_type: bgp_neighbor
    name: "10.0.0.2"
    network_instance: default
    state: present
    config:
      peer_as: 65002
      peer_group: underlay
      admin_state: enable

- name: Delete a static route
  chasewoodard93.srlinux.srlinux_resource:
    host: 172.20.20.101
    username: admin
    password: NokiaSrl1!
    resource_type: static_route
    name: "0.0.0.0/0"
    network_instance: mgmt
    state: absent

- name: Create a network instance
  chasewoodard93.srlinux.srlinux_resource:
    host: 172.20.20.101
    username: admin
    password: NokiaSrl1!
    resource_type: network_instance
    name: tenant-1
    state: present
    config:
      type: ip-vrf
      description: "Tenant 1 VRF"
      admin_state: enable
'''

RETURN = r'''
resource:
  description: The resource that was managed
  returned: always
  type: dict
  sample:
    type: interface
    name: ethernet-1/1
    state: present
commands:
  description: Commands executed on the device
  returned: always
  type: list
  sample: ['set / interface ethernet-1/1 admin-state enable']
before:
  description: Resource state before changes
  returned: when changed
  type: dict
after:
  description: Resource state after changes
  returned: when changed
  type: dict
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.chasewoodard93.srlinux.plugins.module_utils.srlinux import SRLinuxConnection


# Resource type to path mapping
RESOURCE_PATHS = {
    'interface': '/interface',
    'subinterface': '/interface/{parent}/subinterface',
    'network_instance': '/network-instance',
    'bgp_neighbor': '/network-instance/{ni}/protocols/bgp/neighbor',
    'bgp_group': '/network-instance/{ni}/protocols/bgp/group',
    'static_route': '/network-instance/{ni}/static-routes/route',
    'acl': '/acl',
    'routing_policy': '/routing-policy',
    'user': '/system/aaa/authentication/user',
}


def build_commands(resource_type, name, config, network_instance, state):
    """Build SR Linux commands for the resource."""
    commands = []
    base_path = RESOURCE_PATHS.get(resource_type, '')

    # Replace placeholders
    base_path = base_path.replace('{ni}', network_instance)

    if state == 'absent':
        # Delete resource
        if resource_type == 'interface':
            commands.append(f'delete / interface {name}')
        elif resource_type == 'network_instance':
            commands.append(f'delete / network-instance {name}')
        elif resource_type == 'bgp_neighbor':
            commands.append(f'delete / network-instance {network_instance} protocols bgp neighbor {name}')
        elif resource_type == 'static_route':
            commands.append(f'delete / network-instance {network_instance} static-routes route {name}')
        else:
            commands.append(f'delete {base_path} {name}')
    else:
        # Create/update resource
        if resource_type == 'interface':
            for key, value in config.items():
                cmd_key = key.replace('_', '-')
                if isinstance(value, bool):
                    value = 'true' if value else 'false'
                commands.append(f'set / interface {name} {cmd_key} {value}')
        elif resource_type == 'network_instance':
            commands.append(f'set / network-instance {name}')
            for key, value in config.items():
                cmd_key = key.replace('_', '-')
                commands.append(f'set / network-instance {name} {cmd_key} {value}')
        elif resource_type == 'bgp_neighbor':
            for key, value in config.items():
                cmd_key = key.replace('_', '-')
                commands.append(f'set / network-instance {network_instance} protocols bgp neighbor {name} {cmd_key} {value}')
        elif resource_type == 'static_route':
            for key, value in config.items():
                cmd_key = key.replace('_', '-')
                commands.append(f'set / network-instance {network_instance} static-routes route {name} {cmd_key} {value}')
        else:
            for key, value in config.items():
                cmd_key = key.replace('_', '-')
                commands.append(f'set {base_path} {name} {cmd_key} {value}')

    return commands


def main():
    """Main module execution."""

    argument_spec = dict(
        resource_type=dict(type='str', required=True, choices=[
            'interface', 'subinterface', 'network_instance', 'bgp_neighbor',
            'bgp_group', 'static_route', 'acl', 'routing_policy', 'user'
        ]),
        name=dict(type='str', required=True),
        state=dict(type='str', default='present', choices=['present', 'absent']),
        config=dict(type='dict', default={}),
        network_instance=dict(type='str', default='default'),
        host=dict(type='str', required=True),
        port=dict(type='int', default=22),
        username=dict(type='str', default='admin'),
        password=dict(type='str', required=True, no_log=True),
        timeout=dict(type='int', default=30),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    # Get parameters
    resource_type = module.params['resource_type']
    name = module.params['name']
    state = module.params['state']
    config = module.params['config']
    network_instance = module.params['network_instance']

    # Build commands
    commands = build_commands(resource_type, name, config, network_instance, state)

    # Initialize result
    result = {
        'changed': False,
        'resource': {
            'type': resource_type,
            'name': name,
            'state': state
        },
        'commands': commands
    }

    if not commands:
        module.exit_json(**result)

    # Create connection
    connection = SRLinuxConnection(module)

    try:
        if module.check_mode:
            diff = connection.check_config_diff(commands)
            result['diff'] = diff
            result['changed'] = bool(diff.strip())
        else:
            config_result = connection.send_config(commands, commit=True)
            result.update(config_result)

        connection.disconnect()

    except Exception as e:
        connection.disconnect()
        module.fail_json(msg=f'Resource operation failed: {str(e)}')

    module.exit_json(**result)


if __name__ == '__main__':
    main()

