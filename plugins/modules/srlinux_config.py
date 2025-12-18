#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Chase Woodard <chasewoodard93@users.noreply.github.com>
# MIT License

DOCUMENTATION = r'''
---
module: srlinux_config
short_description: Manage Nokia SR Linux configuration
description:
  - This module provides configuration management for Nokia SR Linux devices
  - Supports declarative configuration using set commands
  - Provides idempotent configuration management
  - Supports check mode (dry-run) and diff output
version_added: "1.0.0"
author:
  - Chase Woodard (@chasewoodard93)
options:
  lines:
    description:
      - List of configuration commands to send to the device
      - Commands should be in SR Linux format (e.g., 'set / interface ethernet-1/1 admin-state enable')
      - Commands are applied in candidate mode and committed
    required: false
    type: list
    elements: str
  src:
    description:
      - Path to a file containing configuration commands
      - Can be used instead of or in addition to 'lines'
      - File should contain one command per line
    required: false
    type: path
  backup:
    description:
      - Create a backup of the current configuration before making changes
    required: false
    type: bool
    default: false
  replace:
    description:
      - Replace the entire configuration (not yet implemented)
    required: false
    type: bool
    default: false
  commit:
    description:
      - Commit the configuration changes
      - If false, changes are applied but not committed (useful for validation)
    required: false
    type: bool
    default: true
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
- name: Configure interface description
  chasewoodard93.srlinux.srlinux_config:
    host: 172.20.20.101
    username: admin
    password: NokiaSrl1!
    lines:
      - set / interface ethernet-1/1 description "Uplink to spine1"
      - set / interface ethernet-1/1 admin-state enable

- name: Configure BGP
  chasewoodard93.srlinux.srlinux_config:
    host: "{{ ansible_host }}"
    username: "{{ ansible_user }}"
    password: "{{ ansible_password }}"
    lines:
      - set / network-instance default protocols bgp autonomous-system 65001
      - set / network-instance default protocols bgp router-id 10.0.0.1
      - set / network-instance default protocols bgp admin-state enable

- name: Load configuration from file
  chasewoodard93.srlinux.srlinux_config:
    host: 172.20.20.103
    username: admin
    password: NokiaSrl1!
    src: /path/to/config.txt
    backup: true

- name: Check configuration without committing (dry-run)
  chasewoodard93.srlinux.srlinux_config:
    host: 172.20.20.103
    username: admin
    password: NokiaSrl1!
    lines:
      - set / interface ethernet-1/1 description "Test"
    commit: false
  check_mode: yes
'''

RETURN = r'''
commands:
  description: The set of commands that were sent to the device
  returned: always
  type: list
  sample: ['set / interface ethernet-1/1 admin-state enable', 'set / interface ethernet-1/1 description "Uplink"']
diff:
  description: The configuration diff (what changed)
  returned: when changed
  type: str
  sample: |
    + interface ethernet-1/1 {
    +     admin-state enable
    +     description "Uplink"
    + }
backup_path:
  description: Path to the backup file
  returned: when backup is yes
  type: str
  sample: /path/to/backup/config_backup_2024-01-01.txt
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.chasewoodard93.srlinux.plugins.module_utils.srlinux import SRLinuxConnection
import os


def main():
    """Main module execution."""
    
    argument_spec = dict(
        lines=dict(type='list', elements='str'),
        src=dict(type='path'),
        backup=dict(type='bool', default=False),
        replace=dict(type='bool', default=False),
        commit=dict(type='bool', default=True),
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
    lines = module.params['lines'] or []
    src = module.params['src']
    backup = module.params['backup']
    commit = module.params['commit']
    
    # Load lines from file if src is provided
    if src:
        if not os.path.exists(src):
            module.fail_json(msg=f'Source file not found: {src}')
        
        with open(src, 'r') as f:
            file_lines = [line.strip() for line in f.readlines() if line.strip()]
            lines.extend(file_lines)
    
    # Validate that we have lines to apply
    if not lines:
        module.fail_json(msg='No configuration lines provided. Use "lines" or "src" parameter.')
    
    # Initialize result
    result = {
        'changed': False,
        'commands': [],
        'diff': ''
    }
    
    # Create connection
    connection = SRLinuxConnection(module)
    
    try:
        # Backup if requested
        if backup:
            # TODO: Implement backup functionality
            pass
        
        # Check mode - just check diff without committing
        if module.check_mode:
            diff = connection.check_config_diff(lines)
            result['diff'] = diff
            result['changed'] = bool(diff.strip())
            result['commands'] = lines
        else:
            # Apply configuration
            config_result = connection.send_config(lines, commit=commit)
            result.update(config_result)
        
        # Disconnect
        connection.disconnect()
        
    except Exception as e:
        connection.disconnect()
        module.fail_json(msg=f'Configuration failed: {str(e)}')
    
    # Return results
    module.exit_json(**result)


if __name__ == '__main__':
    main()

