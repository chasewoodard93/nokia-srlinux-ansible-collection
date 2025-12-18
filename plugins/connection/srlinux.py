#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025, Chase Woodard <chasewoodard93@users.noreply.github.com>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = """
---
author: Chase Woodard (@chasewoodard93)
name: srlinux
short_description: Use SSH to connect to Nokia SR Linux devices
description:
  - This connection plugin provides SSH connectivity to Nokia SR Linux devices.
  - It handles the SR Linux CLI modes (operational and configuration).
  - Supports persistent connections for better performance.
version_added: "1.0.0"
options:
  host:
    description:
      - Specifies the remote device FQDN or IP address to establish the SSH connection to.
    default: inventory_hostname
    vars:
      - name: ansible_host
  port:
    type: int
    description:
      - Specifies the port on the remote device that listens for connections.
    default: 22
    ini:
      - section: defaults
        key: remote_port
    vars:
      - name: ansible_port
  network_os:
    description:
      - Configures the device platform network operating system.
    vars:
      - name: ansible_network_os
  remote_user:
    description:
      - The username used to authenticate to the remote device.
    vars:
      - name: ansible_user
  password:
    description:
      - Configures the user password used to authenticate to the remote device.
    vars:
      - name: ansible_password
      - name: ansible_ssh_pass
  timeout:
    type: int
    description:
      - Sets the connection timeout in seconds.
    default: 30
    vars:
      - name: ansible_command_timeout
  persistent_connect_timeout:
    type: int
    description:
      - Configures the persistent connection timeout in seconds.
    default: 30
    ini:
      - section: persistent_connection
        key: connect_timeout
    vars:
      - name: ansible_connect_timeout
  persistent_command_timeout:
    type: int
    description:
      - Configures the persistent command timeout in seconds.
    default: 30
    ini:
      - section: persistent_connection
        key: command_timeout
    vars:
      - name: ansible_command_timeout
"""

import re
import time
import json

from ansible.errors import AnsibleConnectionFailure
from ansible.module_utils._text import to_bytes, to_text
from ansible.plugins.connection import NetworkConnectionBase
from ansible.module_utils.six.moves import StringIO

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False


class Connection(NetworkConnectionBase):
    """SSH connection plugin for Nokia SR Linux devices"""

    transport = 'chasewoodard93.srlinux.srlinux'
    has_pipelining = False

    def __init__(self, play_context, new_stdin, *args, **kwargs):
        super(Connection, self).__init__(play_context, new_stdin, *args, **kwargs)

        if not HAS_PARAMIKO:
            raise AnsibleConnectionFailure("paramiko is required for the srlinux connection plugin")

        self._ssh_client = None
        self._shell = None
        self._connected = False

    def _connect(self):
        """Establish SSH connection to the device"""
        if self._connected:
            return

        self.queue_message('vvv', 'ESTABLISH SR LINUX SSH CONNECTION FOR USER: %s' % self._play_context.remote_user)

        try:
            self._ssh_client = paramiko.SSHClient()
            self._ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connect to device
            self._ssh_client.connect(
                hostname=self._play_context.remote_addr,
                port=self._play_context.port or 22,
                username=self._play_context.remote_user,
                password=self._play_context.password,
                timeout=self.get_option('persistent_connect_timeout'),
                look_for_keys=False,
                allow_agent=False
            )

            # Open interactive shell
            self._shell = self._ssh_client.invoke_shell()
            self._shell.settimeout(self.get_option('persistent_command_timeout'))

            # Wait for initial prompt
            time.sleep(1)
            self._shell.recv(65535)

            self._connected = True
            self.queue_message('vvv', 'SR LINUX SSH CONNECTION ESTABLISHED')

        except Exception as e:
            raise AnsibleConnectionFailure('Failed to connect to %s: %s' % (self._play_context.remote_addr, str(e)))

    def close(self):
        """Close the SSH connection"""
        if self._connected:
            self.queue_message('vvv', 'CLOSING SR LINUX SSH CONNECTION')
            if self._shell:
                self._shell.close()
            if self._ssh_client:
                self._ssh_client.close()
            self._connected = False
            self._shell = None
            self._ssh_client = None

    def exec_command(self, cmd, in_data=None, sudoable=True):
        """Execute a command on the device"""
        if not self._connected:
            self._connect()

        self.queue_message('vvvv', 'EXEC: %s' % cmd)

        try:
            # Send command
            self._shell.send(cmd + '\n')
            time.sleep(0.5)

            # Read output
            output = ''
            while self._shell.recv_ready():
                chunk = self._shell.recv(65535)
                output += to_text(chunk, errors='surrogate_or_strict')
                time.sleep(0.1)

            # Remove command echo and prompt
            lines = output.split('\n')
            if len(lines) > 0:
                lines = lines[1:]  # Remove command echo
            if len(lines) > 0 and lines[-1].strip().startswith('--'):
                lines = lines[:-1]  # Remove prompt

            clean_output = '\n'.join(lines)

            return (0, clean_output, '')

        except Exception as e:
            raise AnsibleConnectionFailure('Failed to execute command: %s' % str(e))

    def send_config(self, config_commands):
        """Send configuration commands to the device"""
        if not self._connected:
            self._connect()

        try:
            # Enter candidate mode
            self._shell.send('enter candidate\n')
            time.sleep(0.5)
            self._shell.recv(65535)

            # Send configuration commands
            for cmd in config_commands:
                self.queue_message('vvvv', 'CONFIG: %s' % cmd)
                self._shell.send(cmd + '\n')
                time.sleep(0.3)
                self._shell.recv(65535)

            # Commit configuration
            self._shell.send('commit now\n')
            time.sleep(1)
            output = ''
            while self._shell.recv_ready():
                chunk = self._shell.recv(65535)
                output += to_text(chunk, errors='surrogate_or_strict')
                time.sleep(0.1)

            # Exit candidate mode
            self._shell.send('quit\n')
            time.sleep(0.5)
            self._shell.recv(65535)

            return output

        except Exception as e:
            # Try to exit candidate mode on error
            try:
                self._shell.send('discard now\n')
                time.sleep(0.5)
                self._shell.send('quit\n')
                time.sleep(0.5)
                self._shell.recv(65535)
            except:
                pass
            raise AnsibleConnectionFailure('Failed to send configuration: %s' % str(e))

    def get(self, command):
        """Execute a show command and return output"""
        return self.exec_command(command)

    def put(self, in_path, out_path):
        """Not implemented for network devices"""
        raise NotImplementedError('put() is not supported for network connections')

    def fetch(self, in_path, out_path):
        """Not implemented for network devices"""
        raise NotImplementedError('fetch() is not supported for network connections')

