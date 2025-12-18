#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Chase Woodard <chasewoodard93@users.noreply.github.com>
# MIT License

DOCUMENTATION = r'''
---
module: srlinux_backup
short_description: Backup Nokia SR Linux device configuration
description:
  - Backup running or startup configuration from Nokia SR Linux devices
  - Saves configuration to a local file with optional timestamp
  - Supports JSON and CLI (flat/set) output formats
version_added: "1.0.0"
author:
  - Chase Woodard (@chasewoodard93)
options:
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
  backup_dir:
    description:
      - Directory path where backup file will be saved
      - Directory will be created if it doesn't exist
    required: true
    type: str
  filename:
    description:
      - Custom filename for the backup
      - If not specified, generates hostname_timestamp.cfg
    required: false
    type: str
  format:
    description:
      - Output format for the backup
      - C(set) for flat CLI set commands (default)
      - C(json) for JSON format
    required: false
    type: str
    choices: ['set', 'json']
    default: set
  config_type:
    description:
      - Type of configuration to backup
      - C(running) for current running configuration
      - C(startup) for saved startup configuration
    required: false
    type: str
    choices: ['running', 'startup']
    default: running
  include_timestamp:
    description:
      - Include timestamp in the filename
    required: false
    type: bool
    default: true
'''

EXAMPLES = r'''
- name: Backup running configuration (set format)
  chasewoodard93.srlinux.srlinux_backup:
    host: 172.20.20.101
    username: admin
    password: NokiaSrl1!
    backup_dir: /backups/srlinux
  register: backup_result

- name: Backup to specific file in JSON format
  chasewoodard93.srlinux.srlinux_backup:
    host: "{{ ansible_host }}"
    username: "{{ ansible_user }}"
    password: "{{ ansible_password }}"
    backup_dir: /backups
    filename: spine1_config.json
    format: json

- name: Backup startup configuration without timestamp
  chasewoodard93.srlinux.srlinux_backup:
    host: 172.20.20.101
    username: admin
    password: NokiaSrl1!
    backup_dir: /var/backups/network
    config_type: startup
    include_timestamp: false
'''

RETURN = r'''
backup_path:
  description: Full path to the backup file
  returned: success
  type: str
  sample: /backups/srlinux/spine1_2024-01-15_143022.cfg
hostname:
  description: Hostname of the backed up device
  returned: success
  type: str
  sample: spine1
config_size:
  description: Size of the backup file in bytes
  returned: success
  type: int
  sample: 15234
config_lines:
  description: Number of configuration lines
  returned: success
  type: int
  sample: 342
changed:
  description: Whether a new backup was created
  returned: always
  type: bool
  sample: true
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.chasewoodard93.srlinux.plugins.module_utils.srlinux import SRLinuxConnection
import os
import re
from datetime import datetime


def get_hostname(connection):
    """Get device hostname."""
    output = connection.execute_command('show version')
    match = re.search(r'Hostname\s+:\s+(\S+)', output)
    return match.group(1) if match else 'srlinux'


def get_config(connection, config_type, format_type):
    """Get configuration from device."""
    if format_type == 'json':
        if config_type == 'running':
            cmd = 'info from running / | as json'
        else:
            cmd = 'info from running / | as json'  # SR Linux uses running as source
    else:
        # Set format (flat CLI commands)
        if config_type == 'running':
            cmd = 'info flat'
        else:
            cmd = 'info flat'

    return connection.execute_command(cmd)


def main():
    """Main module execution."""
    argument_spec = dict(
        host=dict(type='str', required=True),
        port=dict(type='int', default=22),
        username=dict(type='str', default='admin'),
        password=dict(type='str', required=True, no_log=True),
        timeout=dict(type='int', default=30),
        backup_dir=dict(type='str', required=True),
        filename=dict(type='str', required=False),
        format=dict(type='str', choices=['set', 'json'], default='set'),
        config_type=dict(type='str', choices=['running', 'startup'], default='running'),
        include_timestamp=dict(type='bool', default=True),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True
    )

    backup_dir = module.params['backup_dir']
    filename = module.params['filename']
    format_type = module.params['format']
    config_type = module.params['config_type']
    include_timestamp = module.params['include_timestamp']

    # Create backup directory if needed
    if not os.path.exists(backup_dir):
        try:
            os.makedirs(backup_dir)
        except OSError as e:
            module.fail_json(msg=f'Failed to create backup directory: {str(e)}')

    connection = SRLinuxConnection(module)

    try:
        connection.connect()

        # Get hostname for filename
        hostname = get_hostname(connection)

        # Generate filename if not provided
        if not filename:
            extension = 'json' if format_type == 'json' else 'cfg'
            if include_timestamp:
                timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
                filename = f'{hostname}_{timestamp}.{extension}'
            else:
                filename = f'{hostname}.{extension}'

        backup_path = os.path.join(backup_dir, filename)

        # Check mode - don't actually backup
        if module.check_mode:
            module.exit_json(
                changed=True,
                backup_path=backup_path,
                hostname=hostname,
                msg='Backup would be created (check mode)'
            )

        # Get configuration
        config = get_config(connection, config_type, format_type)

        # Write backup file
        with open(backup_path, 'w') as f:
            f.write(config)

        # Get file stats
        file_size = os.path.getsize(backup_path)
        line_count = config.count('\n')

        module.exit_json(
            changed=True,
            backup_path=backup_path,
            hostname=hostname,
            config_size=file_size,
            config_lines=line_count,
            msg=f'Configuration backed up to {backup_path}'
        )

    except Exception as e:
        module.fail_json(msg=f'Backup failed: {str(e)}')
    finally:
        connection.disconnect()


if __name__ == '__main__':
    main()

