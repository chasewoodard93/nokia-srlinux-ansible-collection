#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024, Chase Woodard <chasewoodard93@users.noreply.github.com>
# MIT License

"""
SR Linux Module Utilities

This module provides shared functionality for all SR Linux Ansible modules.
It handles SSH connections, command execution, and configuration management.
"""

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import re
import time
import json

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False


class SRLinuxConnection:
    """
    Manages SSH connections and command execution for Nokia SR Linux devices.
    
    This class provides methods for:
    - Establishing SSH connections
    - Executing commands
    - Managing configuration (candidate mode, commit, discard)
    - Retrieving device state
    """
    
    def __init__(self, module):
        """
        Initialize the SR Linux connection handler.
        
        Args:
            module: AnsibleModule instance with connection parameters
        """
        self.module = module
        self.client = None
        self.shell = None
        self.connected = False
        
        # Connection parameters
        self.host = module.params.get('host') or module.params.get('provider', {}).get('host')
        self.port = module.params.get('port', 22)
        self.username = module.params.get('username') or module.params.get('provider', {}).get('username', 'admin')
        self.password = module.params.get('password') or module.params.get('provider', {}).get('password')
        self.timeout = module.params.get('timeout', 30)
        
        if not HAS_PARAMIKO:
            module.fail_json(msg='paramiko is required but not installed. Install it using: pip install paramiko')
    
    def connect(self):
        """
        Establish SSH connection to SR Linux device.
        
        Returns:
            bool: True if connection successful
            
        Raises:
            Exception: If connection fails
        """
        if self.connected:
            return True
        
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            self.client.connect(
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=False
            )
            
            # Open interactive shell for configuration commands
            self.shell = self.client.invoke_shell()
            self.shell.settimeout(self.timeout)
            
            # Wait for initial prompt and clear buffer
            time.sleep(1)
            self._clear_buffer()
            
            self.connected = True
            return True
            
        except Exception as e:
            self.module.fail_json(msg=f'Failed to connect to {self.host}: {str(e)}')
    
    def disconnect(self):
        """Close SSH connection."""
        if self.shell:
            self.shell.close()
        if self.client:
            self.client.close()
        self.connected = False
    
    def _clear_buffer(self):
        """Clear the shell buffer."""
        if self.shell and self.shell.recv_ready():
            self.shell.recv(65535)

    def _strip_ansi_codes(self, text):
        """
        Remove ANSI escape codes from text.

        Args:
            text: String containing ANSI escape codes

        Returns:
            str: Cleaned text without ANSI codes
        """
        # Remove all ANSI escape sequences comprehensively
        # This handles CSI sequences like [?25h, [0m, [7l, etc.
        text = re.sub(r'\x1b\[\??[0-9;]*[a-zA-Z]', '', text)
        # Remove OSC sequences (like title changes)
        text = re.sub(r'\x1b\].*?\x07', '', text)
        # Remove escape sequences like ESC=, ESC>
        text = re.sub(r'\x1b[=>]', '', text)
        # Remove character set selections
        text = re.sub(r'\x1b\([0-9;]*[a-zA-Z]', '', text)
        # Remove device status report requests
        text = re.sub(r'\x1b\[6n', '', text)
        # Remove bracketed paste mode sequences
        text = re.sub(r'\x1b\[\?2004[hl]', '', text)
        # Remove any remaining control characters except newline, tab, and carriage return
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f]', '', text)

        return text

    def _send_command(self, command, wait_for_prompt=True):
        """
        Send a command to the device shell.

        Args:
            command: Command string to send
            wait_for_prompt: Wait for prompt after command

        Returns:
            str: Command output
        """
        if not self.shell:
            self.module.fail_json(msg='Not connected to device')

        # Send command
        self.shell.send(command + '\n')
        time.sleep(0.5)

        # Collect output
        output = ''
        if wait_for_prompt:
            max_wait = 30  # Maximum wait time in seconds
            start_time = time.time()

            while time.time() - start_time < max_wait:
                if self.shell.recv_ready():
                    chunk = self.shell.recv(65535).decode('utf-8', errors='ignore')
                    output += chunk

                    # Check for prompt (SR Linux prompts end with # or >)
                    # Strip ANSI codes before checking for prompt
                    clean_output = self._strip_ansi_codes(output)
                    if re.search(r'[#>]\s*$', clean_output):
                        break
                time.sleep(0.1)

        return output
    
    def execute_command(self, command):
        """
        Execute a single command in operational mode.

        Args:
            command: Command to execute

        Returns:
            str: Command output
        """
        self.connect()
        output = self._send_command(command)

        # Strip ANSI escape codes
        output = self._strip_ansi_codes(output)

        # Remove echo of command and prompt from output
        lines = output.split('\n')
        # Filter out command echo and prompts
        cleaned_lines = [line for line in lines[1:-1] if not re.match(r'^--\{.*\}--', line)]

        return '\n'.join(cleaned_lines).strip()

    def execute_commands(self, commands):
        """
        Execute multiple commands in operational mode.

        Args:
            commands: List of commands to execute

        Returns:
            list: List of command outputs
        """
        results = []
        for command in commands:
            output = self.execute_command(command)
            results.append(output)
        return results

    def enter_candidate_mode(self):
        """Enter candidate configuration mode."""
        self.connect()
        output = self._send_command('enter candidate')

        if 'candidate' not in output.lower():
            self.module.fail_json(msg='Failed to enter candidate mode')

        return True

    def exit_candidate_mode(self):
        """Exit candidate configuration mode."""
        output = self._send_command('quit')
        return True

    def get_config(self, source='running', format='flat'):
        """
        Retrieve device configuration.

        Args:
            source: Configuration source ('running', 'candidate')
            format: Output format ('flat', 'json', 'hierarchical')

        Returns:
            str: Configuration output
        """
        self.connect()

        # Enter candidate mode to access config
        self.enter_candidate_mode()

        # Build info command based on format
        if format == 'flat':
            command = 'info flat'
        elif format == 'json':
            command = 'info json'
        else:
            command = 'info'

        output = self._send_command(command)
        self.exit_candidate_mode()

        # Strip ANSI escape codes
        output = self._strip_ansi_codes(output)

        # Clean output
        lines = output.split('\n')
        cleaned_lines = [line for line in lines if line.strip() and not re.match(r'^--\{.*\}--', line)]

        return '\n'.join(cleaned_lines).strip()

    def send_config(self, lines, commit=True):
        """
        Send configuration lines to device.

        Args:
            lines: List of configuration commands
            commit: Whether to commit changes (default: True)

        Returns:
            dict: Result with 'changed' and 'commands' keys
        """
        self.connect()
        result = {'changed': False, 'commands': [], 'diff': ''}

        if not lines:
            return result

        # Enter candidate mode
        self.enter_candidate_mode()

        # Send each configuration line
        for line in lines:
            if line.strip():
                output = self._send_command(line)
                result['commands'].append(line)

                # Check for errors
                if 'error' in output.lower() or 'invalid' in output.lower():
                    self.exit_candidate_mode()
                    self.module.fail_json(msg=f'Configuration error: {output}')

        # Get diff before committing
        diff_output = self._send_command('diff')
        result['diff'] = self._clean_diff_output(diff_output)

        # Check if there are actual changes
        # Look for actual configuration changes (lines with + or -)
        has_changes = False
        if result['diff']:
            for line in result['diff'].split('\n'):
                # Check for actual diff markers
                if line.strip().startswith(('+', '-')) and not line.strip().startswith(('+++', '---')):
                    has_changes = True
                    break
                # Also check for SR Linux diff format (lines with actual config)
                if any(keyword in line for keyword in ['interface', 'network-instance', 'protocols', 'system']):
                    if '+' in result['diff'] or '-' in result['diff']:
                        has_changes = True
                        break

        if has_changes:
            result['changed'] = True

            # Commit if requested
            if commit:
                commit_output = self._send_command('commit now')

                if 'error' in commit_output.lower() or 'failed' in commit_output.lower():
                    self.exit_candidate_mode()
                    self.module.fail_json(msg=f'Commit failed: {commit_output}')
        else:
            # No changes detected, discard candidate
            result['changed'] = False
            self._send_command('discard now')

        # Exit candidate mode
        self.exit_candidate_mode()

        return result

    def _clean_diff_output(self, diff_output):
        """
        Clean diff output by removing prompts and extra whitespace.

        Args:
            diff_output: Raw diff output

        Returns:
            str: Cleaned diff output
        """
        # First strip all ANSI escape codes
        diff_output = self._strip_ansi_codes(diff_output)

        lines = diff_output.split('\n')
        cleaned_lines = []

        for line in lines:
            # Skip prompts and empty lines
            if re.match(r'^--\{.*\}--', line):
                continue
            if re.match(r'^A:.*#', line):
                continue
            if line.strip() == 'diff':
                continue
            if not line.strip():
                continue

            cleaned_lines.append(line)

        result = '\n'.join(cleaned_lines).strip()

        # If result is empty or only contains whitespace/control chars, return empty
        if not result or not any(c.isalnum() or c in '+-{}[]' for c in result):
            return ''

        return result

    def check_config_diff(self, lines):
        """
        Check what would change without committing.

        Args:
            lines: List of configuration commands

        Returns:
            str: Diff output
        """
        self.connect()
        self.enter_candidate_mode()

        # Send configuration lines
        for line in lines:
            if line.strip():
                self._send_command(line)

        # Get diff
        diff_output = self._send_command('diff')
        cleaned_diff = self._clean_diff_output(diff_output)

        # Discard changes
        self._send_command('discard now')
        self.exit_candidate_mode()

        return cleaned_diff

