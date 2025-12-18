#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Chase Woodard <chasewoodard93@users.noreply.github.com>
# MIT License

DOCUMENTATION = r'''
---
module: srlinux_command
short_description: Run commands on Nokia SR Linux devices
description:
  - Sends arbitrary commands to an SR Linux device and returns the results
  - This module is useful for running show commands and gathering operational data
  - Commands are executed in operational mode (not configuration mode)
version_added: "1.0.0"
author:
  - Chase Woodard (@chasewoodard93)
options:
  commands:
    description:
      - List of commands to send to the remote SR Linux device
      - Commands are executed in operational mode
    required: true
    type: list
    elements: str
  wait_for:
    description:
      - List of conditions to wait for before returning
      - Each condition is evaluated against the command output
    required: false
    type: list
    elements: str
  match:
    description:
      - The match policy for wait_for conditions
      - C(any) means at least one condition must match
      - C(all) means all conditions must match
    required: false
    type: str
    choices: ['any', 'all']
    default: 'all'
  retries:
    description:
      - Number of retries when waiting for conditions
    required: false
    type: int
    default: 10
  interval:
    description:
      - Interval between retries in seconds
    required: false
    type: int
    default: 1
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
- name: Run show version command
  chasewoodard93.srlinux.srlinux_command:
    host: 172.20.20.101
    username: admin
    password: NokiaSrl1!
    commands:
      - show version

- name: Run multiple show commands
  chasewoodard93.srlinux.srlinux_command:
    host: 172.20.20.101
    username: admin
    password: NokiaSrl1!
    commands:
      - show version
      - show interface brief
      - show network-instance default protocols bgp summary

- name: Run command and wait for specific output
  chasewoodard93.srlinux.srlinux_command:
    host: 172.20.20.101
    username: admin
    password: NokiaSrl1!
    commands:
      - show network-instance default protocols bgp summary
    wait_for:
      - result[0] contains "Established"
    retries: 5
    interval: 2

- name: Get interface state
  chasewoodard93.srlinux.srlinux_command:
    host: "{{ ansible_host }}"
    username: "{{ ansible_user }}"
    password: "{{ ansible_password }}"
    commands:
      - info from state interface ethernet-1/1
  register: interface_state
'''

RETURN = r'''
stdout:
  description: The set of responses from the commands
  returned: always
  type: list
  sample: ['Hostname: spine1...', 'Interface ethernet-1/1...']
stdout_lines:
  description: The value of stdout split into a list
  returned: always
  type: list
  sample: [['Hostname: spine1', 'Chassis Type: 7220 IXR-D2'], ['Interface ethernet-1/1', 'admin-state: enable']]
failed_conditions:
  description: The list of conditionals that failed
  returned: failed
  type: list
  sample: ['result[0] contains "Established"']
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.chasewoodard93.srlinux.plugins.module_utils.srlinux import SRLinuxConnection


def main():
    """Main module execution."""
    
    argument_spec = dict(
        commands=dict(type='list', elements='str', required=True),
        wait_for=dict(type='list', elements='str'),
        match=dict(type='str', choices=['any', 'all'], default='all'),
        retries=dict(type='int', default=10),
        interval=dict(type='int', default=1),
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
    commands = module.params['commands']
    
    # Initialize result
    result = {
        'changed': False,
        'stdout': [],
        'stdout_lines': []
    }
    
    # Create connection
    connection = SRLinuxConnection(module)
    
    try:
        # Execute commands
        for command in commands:
            output = connection.execute_command(command)
            result['stdout'].append(output)
            result['stdout_lines'].append(output.split('\n'))
        
        # Disconnect
        connection.disconnect()
        
    except Exception as e:
        connection.disconnect()
        module.fail_json(msg=f'Failed to execute commands: {str(e)}')
    
    # Return results
    module.exit_json(**result)


if __name__ == '__main__':
    main()

