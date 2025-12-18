# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-01

### Added

#### Modules
- **srlinux_command** - Execute CLI commands on SR Linux devices
  - Support for single and multiple commands
  - Returns structured output in stdout array
- **srlinux_config** - Apply configuration to SR Linux devices
  - Supports `set` and `delete` commands
  - Commit with automatic validation
  - Idempotent operation
- **srlinux_facts** - Gather device facts
  - Collects hostname, version, model, serial
  - Retrieves running configuration
  - Gathers interface information

#### Roles
- **base_config** - Base system configuration
  - Hostname and system information
  - Loopback interface configuration
  - Fabric-facing interface setup
  - Default network instance
- **bgp_underlay** - eBGP IP fabric underlay
  - Peer group configuration
  - Dynamic neighbor setup based on topology
  - IPv4 unicast address family
- **evpn_overlay** - EVPN control plane
  - iBGP EVPN peer groups
  - Route reflector support for spines
  - EVPN address family configuration
- **fabric_facts** - Topology auto-calculation
  - Loopback IP derivation from device index
  - BGP neighbor auto-discovery
  - ASN calculation for spine/leaf roles
- **l2_services** - Layer 2 EVPN services
  - MAC-VRF network instance creation
  - VXLAN VNI configuration
  - EVPN BGP integration
- **l3_services** - Layer 3 EVPN services
  - IP-VRF network instance creation
  - IRB interface configuration
  - Anycast gateway support
  - Route target import/export

#### Connection Plugin
- **srlinux** - SSH-based connection to SR Linux devices
  - Prompt detection with ANSI escape code handling
  - Automatic enter/exit from candidate mode

#### Documentation
- Comprehensive README with quick start guide
- Module documentation with examples
- Role documentation with variables reference

### Tested
- All modules tested on Nokia SR Linux v24.7.1
- Containerlab topology with 2 spines and 4 leafs
- Full integration test suite (9 tests)
  - 3 module tests
  - 6 role tests
- Idempotency verified for all roles

### Requirements
- Ansible >= 2.10.0
- Python >= 3.8
- paramiko (for SSH connections)

---

## [Unreleased]

### Planned
- JSON-RPC API support as alternative to SSH
- Additional validation and pre-check modules
- Backup and restore functionality
- Multi-vendor interoperability testing

