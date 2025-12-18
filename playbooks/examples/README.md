# Example Playbooks

This directory contains example playbooks demonstrating how to use the Nokia SR Linux Ansible Collection roles.

## Playbook Overview

### Day 0/1 Configuration (01-10)

| Playbook | Description | Key Roles Used |
|----------|-------------|----------------|
| `01_system_day0.yml` | Day 0 system configuration | system_ntp, system_dns, system_logging, system_aaa |
| `02_backup_restore.yml` | Configuration backup and restore | config_backup, config_restore, health_check |
| `03_security_hardening.yml` | Security configuration | acl, cpm_filter, system_snmp |
| `04_interfaces_lag.yml` | Interface and LAG setup | interfaces, lag |
| `05_routing_ospf_bfd.yml` | OSPF with BFD | ospf, bfd |
| `06_static_routes_policy.yml` | Static routes and policies | static_routes, routing_policy |
| `07_health_check.yml` | Device health validation | health_check |
| `08_software_upgrade.yml` | Software upgrade workflow | software_upgrade, health_check |
| `09_evpn_fabric.yml` | Full EVPN/VXLAN deployment | All fabric roles |
| `10_day2_operations.yml` | Day 2 operations workflow | config_backup, health_check, srlinux_facts |

### Advanced Features (11-22)

| Playbook | Description | Key Roles Used |
|----------|-------------|----------------|
| `11_esi_multihoming.yml` | EVPN ESI multihoming | esi_multihoming |
| `12_network_instance.yml` | VRF/network-instance management | network_instance |
| `13_ssh_management.yml` | SSH server hardening | ssh_management |
| `14_l2_features.yml` | L2 features configuration | dhcp_relay, storm_control, igmp_snooping, sflow |
| `15_mirroring.yml` | Port mirroring (SPAN) | mirroring |
| `16_isis.yml` | IS-IS routing protocol | isis |
| `17_pim_multicast.yml` | PIM multicast routing | pim |
| `18_segment_routing.yml` | SR-MPLS and SRv6 | segment_routing |
| `19_mpls.yml` | MPLS with LDP/RSVP-TE | mpls |
| `20_event_handler.yml` | Event-driven automation | event_handler |
| `21_vrrp.yml` | VRRP gateway redundancy | vrrp |
| `22_qos_telemetry.yml` | QoS and streaming telemetry | qos, telemetry |

## Usage Examples

### Day 0 System Configuration
```bash
ansible-playbook 01_system_day0.yml -i inventory/hosts.yml
```

### Backup All Devices
```bash
ansible-playbook 02_backup_restore.yml -i inventory/hosts.yml --tags backup
```

### Restore Single Device
```bash
ansible-playbook 02_backup_restore.yml -i inventory/hosts.yml --tags restore -l leaf1 \
  -e "restore_file=/backups/leaf1_backup.json"
```

### Health Check
```bash
ansible-playbook 07_health_check.yml -i inventory/hosts.yml
```

### Software Upgrade Pre-Check
```bash
ansible-playbook 08_software_upgrade.yml -i inventory/hosts.yml --tags precheck
```

### Deploy EVPN Fabric
```bash
ansible-playbook 09_evpn_fabric.yml -i inventory/hosts.yml
```

### Day 2 Operations
```bash
# Full workflow
ansible-playbook 10_day2_operations.yml -i inventory/hosts.yml

# Just backups
ansible-playbook 10_day2_operations.yml -i inventory/hosts.yml --tags backup

# Just health check
ansible-playbook 10_day2_operations.yml -i inventory/hosts.yml --tags health
```

## Customization

Each playbook uses variables that can be customized:

1. **In the playbook**: Modify the `vars:` section directly
2. **Via command line**: Use `-e "variable=value"`
3. **Via inventory**: Define in `group_vars/` or `host_vars/`

## Prerequisites

- Ansible 2.10+
- Python 3.8+
- paramiko library
- Network connectivity to SR Linux devices

## Collection Installation

```bash
ansible-galaxy collection install chasewoodard93.srlinux
```

Or install from GitHub:
```bash
ansible-galaxy collection install git+https://github.com/chasewoodard93/nokia-srlinux-ansible-collection.git
```

