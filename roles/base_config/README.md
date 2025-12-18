# Role: base_config

## Description

This role configures the foundational settings on Nokia SR Linux devices, including:
- System information (hostname, location, contact)
- Loopback interface (system0)
- Physical interfaces with IP addresses
- LLDP for neighbor discovery

This is the **first role** that should be applied to any SR Linux device in the EVPN fabric.

## Requirements

- Ansible 2.9 or higher
- `chasewoodard93.srlinux` collection installed
- SSH access to SR Linux devices
- Credentials (username/password)

## Role Variables

### Required Variables (must be set in inventory)

```yaml
ansible_host: "172.20.20.101"        # Management IP
ansible_user: "admin"                 # SSH username
ansible_password: "NokiaSrl1!"        # SSH password
loopback_ip: "1.1.1.1/32"            # Loopback IP address
interfaces:                           # List of interfaces to configure
  - name: ethernet-1/1
    description: "To spine1"
    ipv4: "10.0.1.0/31"
    admin_state: enable
```

### Optional Variables (have defaults)

```yaml
system_name: "{{ inventory_hostname }}"
system_location: "Data Center"
system_contact: "Network Operations"
dns_servers:
  - 8.8.8.8
  - 8.8.4.4
ntp_servers:
  - 0.pool.ntp.org
  - 1.pool.ntp.org
enable_lldp: true
enable_ipv6: false
```

## Dependencies

None - this is the foundation role.

## Example Playbook

```yaml
---
- name: Configure base settings on all devices
  hosts: all
  gather_facts: no
  
  roles:
    - chasewoodard93.srlinux.base_config
```

## Example Inventory

```yaml
all:
  children:
    spines:
      hosts:
        spine1:
          ansible_host: 172.20.20.101
          loopback_ip: "1.1.1.1/32"
          interfaces:
            - name: ethernet-1/1
              description: "To leaf1"
              ipv4: "10.0.1.0/31"
    leafs:
      hosts:
        leaf1:
          ansible_host: 172.20.20.103
          loopback_ip: "2.2.2.1/32"
          interfaces:
            - name: ethernet-1/31
              description: "To spine1"
              ipv4: "10.0.1.1/31"
  
  vars:
    ansible_user: admin
    ansible_password: NokiaSrl1!
```

## Tags

- `base` - All base configuration tasks
- `system` - System information only
- `interfaces` - Interface configuration only
- `loopback` - Loopback interface only
- `lldp` - LLDP configuration only
- `facts` - Fact gathering only
- `verify` - Verification tasks only

## Example Usage with Tags

```bash
# Configure everything
ansible-playbook site.yml --tags base

# Configure only interfaces
ansible-playbook site.yml --tags interfaces

# Configure only loopback
ansible-playbook site.yml --tags loopback
```

## What This Role Does

1. **System Configuration**
   - Sets system location and contact information
   
2. **Loopback Interface**
   - Enables system0 interface
   - Configures IPv4 address
   - This becomes the router ID for BGP

3. **Physical Interfaces**
   - Configures each interface in the list
   - Sets description
   - Configures IPv4 address
   - Enables the interface

4. **LLDP**
   - Enables LLDP for neighbor discovery
   - Useful for verification and troubleshooting

5. **Verification**
   - Gathers device facts
   - Verifies loopback is up
   - Displays configuration summary

## License

MIT

## Author

chasewoodard93

