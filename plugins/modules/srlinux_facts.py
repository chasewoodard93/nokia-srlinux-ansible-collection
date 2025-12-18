#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Chase Woodard <chasewoodard93@users.noreply.github.com>
# MIT License

DOCUMENTATION = r'''
---
module: srlinux_facts
short_description: Collect facts from Nokia SR Linux devices
description:
  - Collects device information from Nokia SR Linux devices
  - Gathers hardware, software, interface, and network protocol information
  - Returns structured data that can be used in playbooks
version_added: "1.0.0"
author:
  - Chase Woodard (@chasewoodard93)
options:
  gather_subset:
    description:
      - List of fact subsets to gather
      - C(all) gathers all available facts
      - C(hardware) gathers hardware and system information
      - C(interfaces) gathers interface information
      - C(config) gathers configuration information
    required: false
    type: list
    elements: str
    default: ['!config']
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
- name: Gather all facts
  chasewoodard93.srlinux.srlinux_facts:
    host: 172.20.20.101
    username: admin
    password: NokiaSrl1!
    gather_subset: all

- name: Gather only hardware facts
  chasewoodard93.srlinux.srlinux_facts:
    host: "{{ ansible_host }}"
    username: "{{ ansible_user }}"
    password: "{{ ansible_password }}"
    gather_subset:
      - hardware

- name: Gather hardware and interface facts
  chasewoodard93.srlinux.srlinux_facts:
    host: 172.20.20.103
    username: admin
    password: NokiaSrl1!
    gather_subset:
      - hardware
      - interfaces
  register: device_facts

- name: Display hostname
  debug:
    msg: "Device hostname is {{ device_facts.ansible_facts.ansible_net_hostname }}"
'''

RETURN = r'''
ansible_facts:
  description: Dictionary of facts collected from the device
  returned: always
  type: dict
  contains:
    ansible_net_hostname:
      description: Device hostname
      type: str
      sample: spine1
    ansible_net_version:
      description: Software version
      type: str
      sample: v25.10.1
    ansible_net_model:
      description: Device model
      type: str
      sample: 7220 IXR-D2
    ansible_net_serialnum:
      description: Device serial number
      type: str
      sample: Sim Serial No.
    ansible_net_interfaces:
      description: Dictionary of interfaces
      type: dict
      sample: {'ethernet-1/1': {'admin_state': 'enable', 'oper_state': 'up'}}
    ansible_net_config:
      description: Device configuration (if requested)
      type: str
      sample: "interface ethernet-1/1 {...}"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.chasewoodard93.srlinux.plugins.module_utils.srlinux import SRLinuxConnection
import re


class FactsCollector:
    """Collects facts from SR Linux devices."""
    
    def __init__(self, connection):
        self.connection = connection
        self.facts = {}
    
    def collect_hardware_facts(self):
        """Collect hardware and system information."""
        output = self.connection.execute_command('show version')
        
        # Parse version output
        hostname_match = re.search(r'Hostname\s+:\s+(\S+)', output)
        version_match = re.search(r'Software Version\s+:\s+(\S+)', output)
        model_match = re.search(r'Chassis Type\s+:\s+(.+)', output)
        serial_match = re.search(r'Serial Number\s+:\s+(\S+)', output)
        
        if hostname_match:
            self.facts['ansible_net_hostname'] = hostname_match.group(1)
        if version_match:
            self.facts['ansible_net_version'] = version_match.group(1)
        if model_match:
            self.facts['ansible_net_model'] = model_match.group(1).strip()
        if serial_match:
            self.facts['ansible_net_serialnum'] = serial_match.group(1)
        
        return self.facts
    
    def collect_interface_facts(self):
        """Collect interface information."""
        output = self.connection.execute_command('show interface brief')

        interfaces = {}
        # Parse table format output
        lines = output.split('\n')

        # Skip header lines (lines with +---+ or | Port |)
        for line in lines:
            line = line.strip()

            # Skip separator lines and header
            if not line or line.startswith('+') or 'Port' in line or '=====' in line:
                continue

            # Parse data lines that start with |
            if line.startswith('|'):
                # Split by | and clean up
                parts = [p.strip() for p in line.split('|') if p.strip()]

                if len(parts) >= 3:
                    intf_name = parts[0]
                    admin_state = parts[1] if len(parts) > 1 else 'unknown'
                    oper_state = parts[2] if len(parts) > 2 else 'unknown'
                    description = parts[5] if len(parts) > 5 else ''

                    interfaces[intf_name] = {
                        'name': intf_name,
                        'admin_state': admin_state,
                        'oper_state': oper_state,
                        'description': description
                    }

        self.facts['ansible_net_interfaces'] = interfaces
        return self.facts
    
    def collect_config_facts(self):
        """Collect configuration information."""
        config = self.connection.get_config(format='hierarchical')
        self.facts['ansible_net_config'] = config
        return self.facts


def main():
    """Main module execution."""
    
    argument_spec = dict(
        gather_subset=dict(type='list', elements='str', default=['!config']),
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
    gather_subset = module.params['gather_subset']
    
    # Normalize subset
    if 'all' in gather_subset:
        gather_subset = ['hardware', 'interfaces', 'config']
    
    # Remove negated subsets
    gather_subset = [s for s in gather_subset if not s.startswith('!')]
    
    # Initialize result
    result = {
        'changed': False,
        'ansible_facts': {}
    }
    
    # Create connection
    connection = SRLinuxConnection(module)
    collector = FactsCollector(connection)
    
    try:
        # Collect requested facts
        if 'hardware' in gather_subset or not gather_subset:
            collector.collect_hardware_facts()
        
        if 'interfaces' in gather_subset:
            collector.collect_interface_facts()
        
        if 'config' in gather_subset:
            collector.collect_config_facts()
        
        # Set facts
        result['ansible_facts'] = collector.facts
        
        # Disconnect
        connection.disconnect()
        
    except Exception as e:
        connection.disconnect()
        module.fail_json(msg=f'Failed to collect facts: {str(e)}')
    
    # Return results
    module.exit_json(**result)


if __name__ == '__main__':
    main()

