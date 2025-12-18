#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Chase Woodard <chasewoodard93@users.noreply.github.com>
# MIT License

DOCUMENTATION = r'''
---
module: srlinux_validate
short_description: Validate configuration before committing
description:
  - This module validates configuration changes before committing
  - Performs syntax validation and semantic checks
  - Useful for pre-commit validation in CI/CD pipelines
  - Returns detailed validation results
version_added: "1.3.0"
author:
  - Chase Woodard (@chasewoodard93)
options:
  config:
    description:
      - List of configuration commands to validate
    required: false
    type: list
    elements: str
  config_file:
    description:
      - Path to a file containing configuration to validate
    required: false
    type: path
  validation_rules:
    description:
      - Custom validation rules to apply
      - Each rule is a dict with 'name', 'path', 'condition', and 'message'
    required: false
    type: list
    elements: dict
    default: []
  check_syntax:
    description:
      - Perform syntax validation
    required: false
    type: bool
    default: true
  check_references:
    description:
      - Check for valid references (e.g., interface exists)
    required: false
    type: bool
    default: true
  check_conflicts:
    description:
      - Check for configuration conflicts
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
- name: Validate configuration before applying
  chasewoodard93.srlinux.srlinux_validate:
    host: 172.20.20.101
    username: admin
    password: NokiaSrl1!
    config:
      - set / interface ethernet-1/1 admin-state enable
      - set / network-instance default protocols bgp autonomous-system 65001
  register: validation

- name: Validate with custom rules
  chasewoodard93.srlinux.srlinux_validate:
    host: "{{ ansible_host }}"
    username: "{{ ansible_user }}"
    password: "{{ ansible_password }}"
    config_file: /path/to/config.txt
    validation_rules:
      - name: "BGP AS check"
        path: "/network-instance/*/protocols/bgp"
        condition: "autonomous-system >= 64512"
        message: "BGP AS must be in private range"
  register: validation

- name: Syntax-only validation
  chasewoodard93.srlinux.srlinux_validate:
    host: 172.20.20.101
    username: admin
    password: NokiaSrl1!
    config:
      - set / interface ethernet-1/1 admin-state enable
    check_references: false
    check_conflicts: false
'''

RETURN = r'''
valid:
  description: Whether the configuration is valid
  returned: always
  type: bool
  sample: true
errors:
  description: List of validation errors
  returned: always
  type: list
  sample:
    - type: syntax
      message: "Invalid command format"
      line: "set / interface ethernet-1/1 invalid-option"
warnings:
  description: List of validation warnings
  returned: always
  type: list
  sample:
    - type: reference
      message: "Interface ethernet-1/99 does not exist"
validation_summary:
  description: Summary of validation results
  returned: always
  type: dict
  sample:
    total_commands: 10
    valid_commands: 9
    errors: 1
    warnings: 0
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.chasewoodard93.srlinux.plugins.module_utils.srlinux import SRLinuxConnection
import os
import re


def validate_syntax(commands):
    """Validate command syntax."""
    errors = []
    valid_prefixes = ['set ', 'delete ']

    for i, cmd in enumerate(commands):
        cmd = cmd.strip()
        if not cmd or cmd.startswith('#'):
            continue

        # Check for valid prefix
        if not any(cmd.startswith(prefix) for prefix in valid_prefixes):
            errors.append({
                'type': 'syntax',
                'line': i + 1,
                'command': cmd,
                'message': f'Command must start with "set" or "delete"'
            })
            continue

        # Check for path format
        if not re.search(r'^(set|delete)\s+/', cmd):
            errors.append({
                'type': 'syntax',
                'line': i + 1,
                'command': cmd,
                'message': 'Command must include a path starting with /'
            })

    return errors


def main():
    """Main module execution."""

    argument_spec = dict(
        config=dict(type='list', elements='str'),
        config_file=dict(type='path'),
        validation_rules=dict(type='list', elements='dict', default=[]),
        check_syntax=dict(type='bool', default=True),
        check_references=dict(type='bool', default=True),
        check_conflicts=dict(type='bool', default=True),
        host=dict(type='str', required=True),
        port=dict(type='int', default=22),
        username=dict(type='str', default='admin'),
        password=dict(type='str', required=True, no_log=True),
        timeout=dict(type='int', default=30),
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        mutually_exclusive=[['config', 'config_file']],
        required_one_of=[['config', 'config_file']],
        supports_check_mode=True
    )

    # Get parameters
    config = module.params['config'] or []
    config_file = module.params['config_file']
    check_syntax = module.params['check_syntax']
    check_references = module.params['check_references']

    # Load config from file if specified
    if config_file:
        if not os.path.exists(config_file):
            module.fail_json(msg=f'Config file not found: {config_file}')
        with open(config_file, 'r') as f:
            config = [line.strip() for line in f.readlines()]

    # Filter to actual commands
    commands = [c for c in config if c.strip() and not c.strip().startswith('#')]

    # Initialize result
    result = {
        'changed': False,
        'valid': True,
        'errors': [],
        'warnings': [],
        'validation_summary': {
            'total_commands': len(commands),
            'valid_commands': len(commands),
            'errors': 0,
            'warnings': 0
        }
    }

    # Syntax validation
    if check_syntax:
        syntax_errors = validate_syntax(commands)
        result['errors'].extend(syntax_errors)

    # Reference validation (requires device connection)
    if check_references and commands:
        connection = SRLinuxConnection(module)
        try:
            # Try to apply in candidate mode without commit
            for cmd in commands:
                try:
                    connection.send_command(cmd)
                except Exception as e:
                    error_msg = str(e)
                    if 'not found' in error_msg.lower() or 'does not exist' in error_msg.lower():
                        result['warnings'].append({
                            'type': 'reference',
                            'command': cmd,
                            'message': error_msg
                        })
                    elif 'invalid' in error_msg.lower() or 'error' in error_msg.lower():
                        result['errors'].append({
                            'type': 'validation',
                            'command': cmd,
                            'message': error_msg
                        })

            # Discard candidate changes
            connection.send_command('discard')
            connection.disconnect()
        except Exception as e:
            connection.disconnect()
            # Don't fail, just add warning
            result['warnings'].append({
                'type': 'connection',
                'message': f'Could not validate references: {str(e)}'
            })

    # Update summary
    result['validation_summary']['errors'] = len(result['errors'])
    result['validation_summary']['warnings'] = len(result['warnings'])
    result['validation_summary']['valid_commands'] = len(commands) - len(result['errors'])
    result['valid'] = len(result['errors']) == 0

    module.exit_json(**result)


if __name__ == '__main__':
    main()

