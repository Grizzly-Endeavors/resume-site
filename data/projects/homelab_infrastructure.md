# Homelab Infrastructure
**Dates:** Ongoing
**Skills:** Linux System Administration, Debian 13, Docker, Docker Compose, nftables, Cloudflare Tunnel, Caddy, GitHub Actions, systemd, Python, Network Security, CI/CD, Infrastructure as Code

Self-hosted web server infrastructure running on Debian 13 (Trixie), configured for hosting web applications with automated CI/CD deployment. Features custom nftables firewall configuration, Docker networking integration, zero-trust access via Cloudflare Tunnel, and organization-level GitHub Actions runner. Hosts production applications at bearflinn.com. Repo: https://github.com/Grizzly-Endeavors/homelab-optiplex

## Technical Achievements

**Linux System Administration & Network Configuration:**
- Configured Debian 13 (Trixie) server on Linux 6.12.57 kernel for production web hosting
- Implemented static IP configuration (10.0.0.187/24) on eno1 interface with gateway routing
- Built comprehensive infrastructure documentation across 7 detailed technical guides
- Designed infrastructure as code with all configurations version-controlled in git
- Created systematic troubleshooting documentation for DNS, networking, and container issues

**Custom Firewall Architecture with nftables:**
- Architected modern nftables firewall replacing legacy iptables with stateful packet inspection
- Implemented default-deny security policy exposing only SSH (22), HTTP (80), HTTPS (443)
- Built SSH rate limiting protection (max 10 connections/minute) preventing brute-force attacks
- Configured connection tracking for established/related flows with stateful inspection
- Designed NAT masquerading for multiple Docker subnets (172.17.0.0/16, 172.16.0.0/12, 192.168.16.0/20)
- Created forward chain rules for Docker bridge interfaces (docker0 and br-*)
- Implemented firewall rules blocking lateral movement while allowing container internet access

**Docker + nftables Integration:**
- Successfully integrated Docker Engine with nftables firewall solving compatibility challenges
- Disabled Docker's iptables management ("iptables": false in daemon.json) for nftables control
- Implemented custom NAT masquerade rules for container networks in nftables
- Configured explicit Docker network subnets preventing configuration drift
- Built forward chain rules enabling bridge interface communication
- Designed overlay2 storage driver with automatic log rotation (10MB per container)
- Maintained container isolation and security while enabling outbound internet access

**Zero-Trust Access with Cloudflare Tunnel:**
- Architected zero-trust network access eliminating inbound port exposure
- Configured Cloudflare Tunnel for secure outbound-only connectivity with TLS termination at edge
- Built multi-application routing pipeline supporting coaching.bearflinn.com and resume.bearflinn.com
- Designed tunnel-to-proxy architecture routing Cloudflare Tunnel to system-level Caddy
- Implemented end-to-end encrypted traffic flow with no direct server exposure
- Troubleshot DNS resolution and connectivity issues between tunnel and backend services

**Reverse Proxy Configuration with Caddy:**
- Deployed system-level Caddy reverse proxy for domain-based application routing
- Configured HTTP routing to backend containers: coaching.bearflinn.com (port 3000), resume.bearflinn.com (port 3001)
- Implemented bind-mounted Caddyfile from git repository enabling version-controlled configuration
- Built graceful reload capability without dropping active connections
- Designed localhost-based backend routing from Caddy to Docker containers
- Created systemd service integration for automatic startup and monitoring

**Container Orchestration with Docker Compose:**
- Implemented multi-container orchestration for production web applications
- Configured custom Docker bridge networks with explicit subnet definitions
- Built automated database migrations and application setup in deployment workflows
- Designed health validation for service startup and database connectivity
- Created service dependency management with depends_on and health checks
- Implemented volume persistence for PostgreSQL data across container restarts

**CI/CD Automation with GitHub Actions:**
- Deployed organization-level self-hosted GitHub Actions runner (grizzly-endeavors org)
- Built automated Docker-based build and deployment workflows
- Configured runner as systemd service for automatic startup and failure recovery
- Implemented environment configuration generation from 20+ GitHub Secrets at runtime
- Created push-to-deploy workflow triggering on main branch commits
- Designed zero-downtime deployment with health check validation

**Multi-Agent Documentation Sync System:**
- Built Python-based file monitoring system using inotify library for real-time change detection
- Implemented MD5 hash-based change detection preventing infinite sync loops
- Designed debounce mechanism (0.5s) preventing redundant file operations
- Created automated synchronization of AI agent instruction files (CLAUDE.md, GEMINI.md, AGENTS.md)
- Deployed as systemd service with automatic startup and failure recovery
- Maintained consistency across multiple documentation files automatically

**Security Hardening & Best Practices:**
- Implemented SSH authentication with ed25519 keys and disabled password authentication
- Configured minimal attack surface with only essential ports exposed
- Built container isolation with network-level separation and firewall integration
- Designed default-deny firewall policy requiring explicit allow rules
- Created non-root Docker user configurations for container security
- Implemented proper permission management in deployed containers
- Excluded sensitive credentials via .gitignore with only configuration documented

**Infrastructure Documentation:**
- Authored comprehensive documentation across 7 technical guides totaling 1000+ lines
- Created firewall configuration guide with nftables rules and security policies
- Documented Docker setup including installation, networking, and firewall integration
- Built Caddy reverse proxy guide with routing configuration and TLS setup
- Wrote Cloudflare Tunnel documentation with troubleshooting procedures
- Developed GitHub Actions runner setup and organization migration guides
- Designed agent synchronization documentation with implementation details

**Service Management with systemd:**
- Configured GitHub Actions runner as systemd service with automatic restart
- Built Caddy reverse proxy service integration with system-level deployment
- Implemented agent documentation sync as systemd service
- Designed service dependencies ensuring proper startup ordering
- Created monitoring and failure recovery mechanisms
- Built graceful service reload capabilities without downtime

## Architecture & Code Quality

**Network Architecture:**
- Three-tier routing: Cloudflare Tunnel → Caddy Reverse Proxy → Docker Containers
- Zero-trust access with no inbound ports exposed
- TLS termination at Cloudflare edge with end-to-end encryption
- Container isolation with custom bridge networks

**Security Design:**
- Defense in depth: firewall + container isolation + minimal exposure
- Default-deny policy requiring explicit allow rules
- Rate limiting on SSH preventing brute-force attacks
- Stateful packet inspection with connection tracking

**Infrastructure as Code:**
- All configurations version-controlled in git repository
- Documented, reproducible server configurations
- Systematic change tracking with git history
- Separation of code and credentials

**Operational Excellence:**
- Automated deployments with GitHub Actions
- Health checks and validation in deployment pipeline
- Comprehensive documentation for all components
- Structured troubleshooting guides

This project demonstrates enterprise-grade infrastructure engineering, Linux system administration, network security, container orchestration, and DevOps automation. Highlights production deployment best practices, security hardening, and comprehensive technical documentation.
