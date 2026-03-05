# Home Lab Kubernetes Infrastructure
**Dates:** Ongoing
**Skills:** Kubernetes, Ansible, Docker, Helm, Calico CNI, Caddy, ZFS, NFS, PostgreSQL, GitHub Actions, Bash Scripting, Kustomize, NetBird VPN, Let's Encrypt, Cloudflare DNS, nftables, Infrastructure as Code

Bare-metal Kubernetes cluster on four repurposed machines (14 cores, 104GB RAM, 11.5TB storage) fully managed through Infrastructure as Code. Connected via mesh VPN to a cloud proxy, providing a self-hosted platform where pushing code to any repository results in automatic build, test, and deployment — no external CI/CD service, no managed Kubernetes, no cloud vendor runtime costs. A new application goes from empty repository to live at `*.bearflinn.com` with valid TLS in under 20 minutes.

Repo: https://github.com/Grizzly-Endeavors/lab-iac

## Technical Achievements

**Bare-Metal Kubernetes Cluster:**
- Provisioned 4-node cluster via kubeadm across repurposed hardware: Dell Inspiron (control plane, 8GB), MSI laptop (32GB, GTX 1060), Tower PC (32GB, 9.3TB storage, GTX 1060), Dell Optiplex (32GB)
- Configured Calico CNI with dual-stack IPv4/IPv6 and BGP mesh between nodes
- Solved bare-metal IP autodetection pitfall configuring `can-reach=8.8.8.8` to prefer LAN interface over VPN tunnels
- Implemented node labeling by workload role (storage, observability, general) for targeted scheduling

**Ansible Configuration Management (13 Playbooks, 8 Roles):**
- Designed sequential playbook chain for full cluster provisioning: baseline OS setup, control plane init, worker join, health validation
- Built 8 reusable roles covering k8s-prerequisites, k8s-packages, k8s-control-plane, k8s-worker, caddy, postgresql-server, garage-server, and tower-storage-setup
- Created idempotent infrastructure service playbooks safe to re-run: proxy VPS, storage, PostgreSQL, S3 storage
- Implemented Ansible Vault encryption for all secrets with single `.vault_pass` file (git-ignored)
- Templated configurations via Jinja2: Caddyfiles, postgresql.conf, pg_hba.conf, garage.toml, systemd overrides, Docker Compose files, backup scripts

**Self-Hosted CI/CD Pipeline:**
- Built custom GitHub Actions runner Docker image with Docker-in-Docker, Helm, kubectl, Rust (with aarch64 cross-compilation), Node.js, and GitHub CLI pre-installed
- Deployed runners in-cluster with auto-scaling (1-4 replicas) via Horizontal Pod Autoscaler based on workflow demand
- Configured cluster-scoped RBAC allowing runners to create namespaces, deploy workloads, and manage secrets
- Established private container registry inside the cluster — images never leave the local network
- Enabled push-to-deploy workflow: push to main triggers build, push to registry, Helm deploy automatically

**Zero-Touch TLS & Routing:**
- Configured Hetzner VPS running Caddy with wildcard certificates for `*.bearflinn.com` via Cloudflare DNS-01 challenges
- Established NetBird mesh VPN tunneling traffic from VPS to cluster control plane with no home network ports exposed
- Deployed NGINX Ingress Controller on NodePorts routing requests to Kubernetes services
- Implemented cert-manager for automated certificate lifecycle management
- Designed system where adding a Kubernetes Ingress resource with a hostname is the only step needed to make a new application publicly reachable

**Multi-Tier Storage Architecture:**
- Configured Tower PC as storage backbone with three tiers: block (NFS), object (S3), and relational (PostgreSQL)
- Built ZFS RAID-Z1 pool across 3x2TB HDDs (~4TB usable) for resilient object storage via Garage S3-compatible API
- Deployed NFS dynamic provisioner enabling Kubernetes PVCs to automatically provision NFS-backed volumes
- Implemented bcache caching layer on NFS exports for improved read performance
- Set up per-application S3 buckets and access keys with read-only capability for analytics

**PostgreSQL Database Service:**
- Deployed containerized PostgreSQL 16 on Tower PC with TLS client certificates for encrypted connections
- Installed pgvector extension for vector embedding operations used by application workloads
- Automated daily backups via cron with Ansible-managed backup scripts
- Exposed database to cluster as Kubernetes ExternalName service
- Configured separate databases and users per application (coaching, resume, family dashboard)

**Network Security:**
- Implemented zero-trust VPN tunneling via NetBird mesh connecting all nodes and VPS proxy
- Managed nftables firewall rules via Ansible with specific rules for NetBird-to-NodePort forwarding
- Configured UFW and fail2ban on the VPS proxy for defense-in-depth
- Enforced no public port exposure on home network — all traffic enters through VPN tunnel

**Idempotent Infrastructure Scripts (13 Scripts):**
- Created shell scripts for addon installation: cert-manager, ingress-nginx, NFS provisioner, GitHub runner, PostgreSQL, Garage S3
- Built runner image build-and-push script for custom CI/CD runner maintenance
- Implemented containerd insecure registry configuration for private registry access
- Designed all scripts with `set -euo pipefail` for safety and idempotent execution

**Operational Documentation:**
- Wrote architecture documentation covering node specs, network topology, and technology decisions
- Created deployment guide with patterns for secrets management, registry operations, and Ingress configuration
- Built operational runbooks with troubleshooting procedures, recovery steps, and health checks
- Documented S3 and PostgreSQL integration guides with code examples for Python, Node.js, and Go

## Architecture & Code Quality

**Infrastructure as Code Discipline:**
- Every machine configured exclusively through Ansible — no manual SSH configuration
- Kubernetes manifests managed via Kustomize with environment overlays
- Helm used for community charts (ingress-nginx, NFS provisioner, cert-manager)
- All changes documented; any non-IaC modifications explicitly recorded

**Repository Organization:**
- `ansible/` — 13 playbooks, 8 roles, inventory, group vars, vault-encrypted secrets, Jinja2 templates
- `kubernetes/` — Kustomize base manifests (registry, runner, PostgreSQL, Garage), Helm values
- `docker/` — Custom GitHub runner Dockerfile with multi-tool installation
- `scripts/` — 13 idempotent shell scripts for Helm installs and node configuration
- `docs/` — Architecture decisions, deployment guide, operational runbooks, integration guides

**Deployed Services:**
- Portfolio landing page (static site)
- Interactive AI resume (full-stack with PostgreSQL + pgvector)
- Overwatch coaching platform (full-stack with PostgreSQL)
- Family dashboard (full-stack with Infisical secrets management)

This project demonstrates production-grade Kubernetes administration, comprehensive Infrastructure as Code practices, self-hosted CI/CD pipeline design, and multi-tier storage architecture — all on bare-metal hardware without external cloud dependencies.