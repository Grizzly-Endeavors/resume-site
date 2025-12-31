# Homelab Infrastructure Configuration

Self-hosted web server infrastructure running on Debian 13 (Trixie), configured for hosting web applications with automated CI/CD deployment.

## 🏗️ Infrastructure Overview

**Server Specs:**
- **OS**: Debian 13 (Trixie) - Linux 6.12.57
- **Networking**: Static IP configuration with nftables firewall
- **Containerization**: Docker Engine with custom network configuration
- **Deployment**: GitHub Actions self-hosted runner
- **Tunneling**: Cloudflare Tunnel for secure public access

## 🔒 Security Features

- **Firewall**: nftables with default-deny policy
- **SSH Protection**: Rate limiting (max 10 connections/minute)
- **Container Isolation**: Custom Docker bridge networks with NAT
- **Stateful Packet Inspection**: Connection tracking for established flows
- **Minimal Attack Surface**: Only essential ports exposed (22, 80, 443)

## 📚 Documentation

Comprehensive documentation for all infrastructure components:

- **[Firewall Configuration](docs/firewall-summary.md)** - Complete nftables setup, NAT rules, and security policies
- **[Docker Setup](docs/docker-setup.md)** - Container runtime configuration, networking, and firewall integration
- **[Caddy Reverse Proxy](docs/caddy-setup.md)** - System-level reverse proxy routing and TLS configuration
- **[Cloudflare Tunnel](docs/cloudflare-tunnel.md)** - Zero-trust tunnel configuration and routing to Caddy
- **[GitHub Actions Runner](docs/github-org-migration.md)** - Organization-level CI/CD runner setup
- **[Agent Docs Sync](docs/agent-sync.md)** - Multi-file documentation synchronization system
- **[Infrastructure TODO](TODO.md)** - Planned improvements and future work

## 🛠️ Key Technologies

- **nftables** - Modern Linux firewall with stateful filtering
- **Docker** - Container runtime with custom networking
- **Docker Compose** - Multi-container orchestration
- **GitHub Actions** - CI/CD automation with self-hosted runner
- **Cloudflare Tunnel** - Zero-trust network access
- **systemd** - Service management and monitoring

## 🎯 Current Features

### Network & Access Layer
- **Static IP**: `10.0.0.187/24` on interface eno1 with gateway routing
- **Zero-Trust Access**: Cloudflare Tunnel for secure outbound-only connectivity
- **Reverse Proxy**: Caddy system-level proxy with domain-based routing
- **Firewall**: nftables with SSH rate limiting and connection tracking
- **NAT Configuration**: Masquerading for Docker containers and custom subnets

### Container & Application Hosting
- **Docker Engine**: overlay2 storage driver with automatic log rotation (10MB per container)
- **Custom Networks**: Multiple Docker bridge networks with explicit NAT rules
- **Application Routing**: Caddy routes `coaching.bearflinn.com` (port 3000) and `resume.bearflinn.com` (port 3001)
- **Secure Connectivity**: End-to-end encrypted via Cloudflare Tunnel (TLS termination at edge)

### CI/CD & Automation
- **GitHub Actions**: Organization-level self-hosted runner (grizzly-endeavors org)
- **Automated Deployments**: Docker-based build and deployment workflows
- **Agent Documentation**: Synchronized CLAUDE.md, GEMINI.md, AGENTS.md files
- **Infrastructure as Code**: All system configurations stored in git repository

### Security & Hardening
- **SSH Protection**: Rate limiting (max 10 new connections/minute) with ed25519 key authentication
- **Default-Deny Firewall**: Only SSH (22), HTTP (80), HTTPS (443) exposed; blocks lateral movement
- **Stateful Tracking**: Connection state inspection for established/related flows
- **Container Isolation**: Network-level separation with firewall integration

## 📁 Repository Structure

```
.
├── README.md                      # This file - infrastructure overview
├── CLAUDE.md                      # Claude Code AI agent configuration
├── GEMINI.md                      # Gemini AI agent configuration
├── AGENTS.md                      # Other AI agents configuration
├── TODO.md                        # Infrastructure improvements roadmap
├── docs/
│   ├── firewall-summary.md        # nftables configuration and rules
│   ├── docker-setup.md            # Docker installation, setup, and networking
│   ├── caddy-setup.md             # Caddy reverse proxy configuration
│   ├── cloudflare-tunnel.md       # Cloudflare Tunnel setup and troubleshooting
│   ├── github-org-migration.md    # GitHub organization runner migration
│   ├── github-runner-setup.md     # GitHub Actions runner documentation
│   └── agent-sync.md              # Multi-file documentation sync system
└── caddy/                         # Caddy configuration (bind mounted from /etc/caddy)
    └── Caddyfile                  # HTTP routing rules
```

## 🚀 Skills Demonstrated

- **Linux System Administration** - Debian server configuration and maintenance
- **Network Security** - Firewall configuration, NAT, and connection tracking
- **Container Orchestration** - Docker networking and custom bridge configurations
- **Infrastructure as Code** - Documented, reproducible server configurations
- **CI/CD** - Automated deployment pipelines with GitHub Actions
- **Troubleshooting** - DNS resolution, network connectivity, and container issues
- **Technical Documentation** - Comprehensive guides for all infrastructure components

## 🔍 Notable Implementations

### Docker + nftables Integration
Successfully integrated Docker with nftables firewall:
- Disables Docker's iptables management (`"iptables": false` in daemon.json)
- Implements custom NAT masquerade rules for container networks (172.17.0.0/16, 172.16.0.0/12, 192.168.16.0/20)
- Configures forward chain rules for bridge interfaces (docker0 and br-*)
- Explicitly defines Docker network subnets to prevent configuration drift
- Maintains security while enabling container internet access

### Cloudflare Tunnel + Caddy Architecture
Designed zero-trust application delivery pipeline:
- Cloudflare Tunnel handles TLS termination at edge (no inbound ports exposed)
- System-level Caddy reverse proxy routes to backend containers via localhost
- Supports multiple applications: coaching website (port 3000), resume website (port 3001)
- Bind-mounted Caddyfile from git repository enables version-controlled configuration
- Graceful reload capability without dropping connections

### Multi-Agent Documentation Sync
Automated synchronization of AI agent instruction files:
- Python-based file monitoring using inotify library
- MD5 hash-based change detection to prevent infinite sync loops
- Debounce mechanism (0.5s) prevents redundant operations
- Systemd service for automatic startup and failure recovery
- Maintains consistency across CLAUDE.md, GEMINI.md, AGENTS.md

## 📊 System Status

- **Uptime**: Active production server
- **Services**: All services running and monitored
- **Security**: Firewall active, SSH rate limiting enabled
- **Containers**: Multi-container applications deployed via Docker Compose
- **Documentation**: Kept current with all system changes

## 🔗 Related Projects

- [Overwatch Coaching Website](https://github.com/Grizzly-Endeavors/coaching-website) - Next.js application deployed on this infrastructure
- [AI-Powered Personal Resume](https://github.com/Grizzly-Endeavors/resume-site)

---

**Note**: Sensitive credentials and tokens are excluded via `.gitignore`. This repository contains only configuration documentation and non-sensitive infrastructure code.
