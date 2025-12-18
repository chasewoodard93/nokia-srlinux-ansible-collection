# Nokia SR Linux Ansible Collection

![Ansible](https://img.shields.io/badge/ansible-%3E%3D2.10-blue)
![Python](https://img.shields.io/badge/python-%3E%3D3.8-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Ansible collection for automating Nokia SR Linux network devices in modern data center environments.

## 🎯 **Description**

This collection provides comprehensive automation capabilities for Nokia SR Linux devices, including:

- **Custom Modules** - Python-based modules for configuration management
- **Connection Plugins** - SR Linux JSON-RPC API integration
- **Roles** - Reusable templates for common deployment scenarios
- **Playbooks** - Complete automation workflows for EVPN spine/leaf architecture

## ✨ **Features**

- ✅ **Configuration Management** - Declarative device configuration
- ✅ **Command Execution** - Run CLI commands programmatically
- ✅ **Facts Gathering** - Collect device information
- ✅ **EVPN/VXLAN** - Full support for modern data center overlays
- ✅ **BGP Automation** - eBGP underlay and iBGP overlay
- ✅ **L2/L3 Services** - MAC-VRF and IP-VRF automation
- ✅ **Idempotent** - Safe to run multiple times
- ✅ **Well-Documented** - Comprehensive examples and guides

## 📦 **Installation**

### **From Ansible Galaxy** (when published)

```bash
ansible-galaxy collection install chasewoodard93.srlinux
```

### **From Source** (development)

```bash
cd /path/to/this/collection
ansible-galaxy collection build
ansible-galaxy collection install chasewoodard93-srlinux-*.tar.gz
```

## 📋 **Requirements**

- **Ansible:** 2.10 or higher
- **Python:** 3.8 or higher
- **Nokia SR Linux:** Any version (tested with containerlab)
- **Network Access:** SSH or JSON-RPC API access to devices

### **Python Dependencies**

Install required Python packages:

```bash
pip install -r requirements.txt
```

## 🚀 **Quick Start**

### **1. Create Inventory**

```yaml
# inventory/hosts.yml
all:
  children:
    spines:
      hosts:
        spine1:
          ansible_host: 172.20.20.101
        spine2:
          ansible_host: 172.20.20.102
    leafs:
      hosts:
        leaf1:
          ansible_host: 172.20.20.103
        leaf2:
          ansible_host: 172.20.20.104
  vars:
    ansible_user: admin
    ansible_password: NokiaSrl1!
    ansible_network_os: nokia.srlinux.srlinux
    ansible_connection: network_cli
```

### **2. Run a Playbook**

```bash
ansible-playbook -i inventory/hosts.yml playbooks/01_base_config.yml
```

## 📚 **Documentation**

- **[Modules Documentation](docs/modules/)** - Detailed module reference
- **[Roles Documentation](docs/roles/)** - Role usage guides
- **[Playbook Examples](docs/playbooks/)** - Complete playbook examples
- **[Development Guide](DEVELOPMENT.md)** - Contributing guidelines

## 🏗️ **Collection Contents**

### **Modules**

| Module | Description |
|--------|-------------|
| `srlinux_config` | Manage device configuration |
| `srlinux_command` | Execute CLI commands |
| `srlinux_facts` | Gather device facts |

### **Roles**

| Role | Description |
|------|-------------|
| `base_config` | System configuration (hostname, interfaces, loopbacks) |
| `bgp_underlay` | eBGP IP fabric for underlay routing |
| `evpn_overlay` | EVPN/VXLAN overlay control plane |
| `fabric_facts` | Auto-calculate fabric topology (loopbacks, neighbors, ASNs) |
| `l2_services` | MAC-VRF L2 EVPN services |
| `l3_services` | IP-VRF/IRB L3 EVPN services |

### **Playbooks**

| Playbook | Description |
|----------|-------------|
| `01_base_config.yml` | Deploy base system configuration |
| `02_underlay_bgp.yml` | Deploy IP fabric underlay |
| `03_evpn_overlay.yml` | Deploy EVPN overlay |
| `04_l2_services.yml` | Deploy L2 EVPN services |
| `05_l3_services.yml` | Deploy L3 EVPN services |
| `site.yml` | Master playbook (runs all) |

## 💡 **Example Usage**

### **Using Modules**

```yaml
- name: Configure interface
  chasewoodard93.srlinux.srlinux_config:
    lines:
      - set / interface ethernet-1/1 admin-state enable
      - set / interface ethernet-1/1 description "Uplink to spine1"
```

### **Using Roles**

```yaml
- name: Deploy EVPN overlay
  hosts: leafs
  roles:
    - chasewoodard93.srlinux.evpn_overlay
```

## 🧪 **Testing**

Run integration tests:

```bash
ansible-test integration
```

## 📄 **License**

MIT

## 👤 **Author**

Chase Woodard (chasewoodard93@users.noreply.github.com)

## 🤝 **Contributing**

Contributions are welcome! Please see [DEVELOPMENT.md](DEVELOPMENT.md) for guidelines.

## 🔗 **Links**

- **Repository:** https://github.com/chasewoodard93/nokia-srlinux-ansible-collection
- **Issues:** https://github.com/chasewoodard93/nokia-srlinux-ansible-collection/issues
- **Nokia SR Linux:** https://learn.srlinux.dev/
- **Ansible Collections:** https://docs.ansible.com/ansible/latest/dev_guide/developing_collections.html
