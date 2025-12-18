#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Chase Woodard <chasewoodard93@users.noreply.github.com>
# MIT License

DOCUMENTATION = r'''
---
module: srlinux_compare
short_description: Compare running configuration with intended configuration
description:
  - This module compares the running configuration with an intended configuration
  - Useful for configuration drift detection and compliance checking
  - Returns detailed diff showing what would change
  - Supports various output formats
version_added: "1.3.0"
author:
  - Chase Woodard (@chasewoodard93)
options:
  intended_config:
    description:
      - List of configuration commands representing the intended state
    required: false
    type: list
    elements: str
  intended_file:
    description:
      - Path to a file containing the intended configuration
    required: false
    type: path
  path:
    description:
      - Specific configuration path to compare
      - If not specified, compares entire configuration
    required: false
    type: str
    default: /
  output_format:
    description:
      - Format for the comparison output
    required: false
    type: str
    choices: [diff, json, yaml]
    default: diff
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
- name: Compare running config with intended
  chasewoodard93.srlinux.srlinux_compare:
    host: 172.20.20.101
    username: admin
    password: NokiaSrl1!
    intended_config:
      - set / interface ethernet-1/1 admin-state enable
      - set / interface ethernet-1/1 description "Uplink"
  register: config_diff

- name: Check for configuration drift
  chasewoodard93.srlinux.srlinux_compare:
    host: "{{ ansible_host }}"
    username: "{{ ansible_user }}"
    password: "{{ ansible_password }}"
    intended_file: /path/to/golden_config.txt
    path: /network-instance/default/protocols/bgp
  register: bgp_drift

- name: Get comparison in JSON format
  chasewoodard93.srlinux.srlinux_compare:
    host: 172.20.20.101
    username: admin
    password: NokiaSrl1!
    intended_config:
      - set / system name host-name leaf1
    output_format: json
  register: comparison
'''

RETURN = r'''
has_drift:
  description: Whether there is configuration drift
  returned: always
  type: bool
  sample: true
diff:
  description: The configuration difference
  returned: always
  type: str
  sample: |
    - interface ethernet-1/1 admin-state disable
    + interface ethernet-1/1 admin-state enable
missing:
  description: Configuration items missing from running config
  returned: always
  type: list
  sample: ['set / interface ethernet-1/1 description "Uplink"']
extra:
  description: Configuration items in running config but not in intended
  returned: always
  type: list
  sample: ['set / interface ethernet-1/2 admin-state enable']
running_config:
  description: Current running configuration (for the specified path)
  returned: when output_format is json or yaml
  type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.chasewoodard93.srlinux.plugins.module_utils.srlinux import SRLinuxConnection
import os


def main():
    """Main module execution."""

    argument_spec = dict(
        intended_config=dict(type='list', elements='str'),
        intended_file=dict(type='path'),
        path=dict(type='str', default='/'),
        output_format=dict(type='str', default='diff', choices=['diff', 'json', 'yaml']),
        host=dict(type='str', required=True),
        port=dict(type='int', default=22),
        username=dict(type='str', default='admin'),
        password=dict(type='str', required=True, no_log=True),
        timeout=dict(type='int', default=30),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[['intended_config', 'intended_file']],
        required_one_of=[['intended_config', 'intended_file']],
        supports_check_mode=True
    )

    # Get parameters
    intended_config = module.params['intended_config'] or []
    intended_file = module.params['intended_file']
    config_path = module.params['path']
    output_format = module.params['output_format']

    # Load intended config from file if specified
    if intended_file:
        if not os.path.exists(intended_file):
            module.fail_json(msg=f'Intended config file not found: {intended_file}')
        with open(intended_file, 'r') as f:
            intended_config = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]

    # Initialize result
    result = {
        'changed': False,
        'has_drift': False,
        'diff': '',
        'missing': [],
        'extra': [],
        'path': config_path
    }

    # Create connection
    connection = SRLinuxConnection(module)

    try:
        # Get running configuration
        running_output = connection.send_command(f'info flat {config_path}')
        running_lines = set()
        for line in running_output.split('\n'):
            line = line.strip()
            if line and line.startswith('set '):
                running_lines.add(line)

        # Normalize intended config
        intended_lines = set()
        for line in intended_config:
            line = line.strip()
            if line and line.startswith('set '):
                intended_lines.add(line)

        # Compare
        missing = intended_lines - running_lines
        extra = running_lines - intended_lines

        result['missing'] = sorted(list(missing))
        result['extra'] = sorted(list(extra))
        result['has_drift'] = bool(missing or extra)

        # Build diff output
        diff_lines = []
        for line in sorted(missing):
            diff_lines.append(f'+ {line}')
        for line in sorted(extra):
            diff_lines.append(f'- {line}')
        result['diff'] = '\n'.join(diff_lines)

        if output_format in ['json', 'yaml']:
            result['running_config'] = running_output

        connection.disconnect()

    except Exception as e:
        connection.disconnect()
        module.fail_json(msg=f'Configuration comparison failed: {str(e)}')

    module.exit_json(**result)


if __name__ == '__main__':
    main()

