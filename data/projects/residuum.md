# Residuum (Personal AI Agent Framework)
**Dates:** Ongoing
**Skills:** Rust, Tokio, Axum, WebSocket, LLM Integration, Anthropic API, OpenAI API, Google Gemini, Ollama, BM25 Search, Vector Embeddings, SQLite, Tantivy, Discord Bot (Serenity), Telegram Bot (Teloxide), MCP (Model Context Protocol), YAML Configuration, AES-GCM Encryption, Async/Await, Systems Architecture

A personal AI agent framework built in Rust that eliminates session boundaries. One agent, continuous memory, every channel. Features observational memory compression that keeps conversation history in context at all times, multi-channel convergence (CLI, Discord, Telegram, webhooks) into a single continuous thread, and YAML-driven pulse scheduling for cost-efficient proactive behavior. Available at residuum.bearflinn.com.

Repo: https://github.com/Grizzly-Endeavors/residuum

## Technical Achievements

**Observational Memory System:**
- Engineered two-tier compression pipeline: Observer extracts interaction pairs at soft/force thresholds, Reflector consolidates observation logs into dense summaries
- Designed continuous context strategy where compressed observations live in the LLM context window at all times — no retrieval step for recent history
- Built interaction-pair chunking that extracts user-assistant conversation pairs while stripping tool I/O noise
- Implemented persistent episode storage with raw transcripts, observation archives, and indexed chunks organized by date (`memory/episodes/YYYY-MM/DD/`)

**Hybrid Memory Search (BM25 + Vector):**
- Integrated Tantivy full-text search engine for BM25 keyword matching across episode history
- Built vector embedding search using sqlite-vec with configurable embedding providers (OpenAI, Ollama, Gemini)
- Designed hybrid ranking combining lexical and semantic similarity for deep retrieval of older episodes
- Created 1,945-line search module handling indexing, querying, and result ranking

**Multi-Channel Gateway:**
- Architected four message sources — CLI (Rustyline REPL), Discord (Serenity), Telegram (Teloxide), HTTP webhooks — all feeding the same agent, same memory, same thread
- Built WebSocket protocol for real-time bidirectional communication with web clients
- Implemented embedded Axum web server with static frontend assets compiled into the binary via rust-embed
- Designed channel normalization layer ensuring message format consistency regardless of source
- Created interrupt-based message delivery routing all channels into a single agent message feed

**YAML-Driven Pulse Scheduling:**
- Designed HEARTBEAT.yml configuration with pulse definitions, cron-style schedules, active hours, and task lists
- Built gateway-side timing evaluation — the LLM only fires when a pulse is due, costing zero tokens on idle cycles
- Implemented CHANNELS.yml declarative notification routing controlling where pulse results land per task
- Created cost-optimized scheduling: email scans, deployment checks, daily reviews each defined in a few lines of YAML

**SubAgent Background Task System:**
- Engineered background agent delegation running on tokio tasks with semaphore-based concurrency control
- Implemented automatic model tiering: small (cheap/fast) to medium (balanced) to large (frontier) with fallback chains
- Built minimal context assembly for subagents (prompt + USER.md + ENVIRONMENT.md + active projects)
- Designed fire-and-forget execution with transcript persistence and result routing back to the main agent's message queue

**Projects Context System:**
- Created self-describing project folders with PROJECT.md (YAML frontmatter + markdown body) and scoped subdirectories (notes/, references/, workspace/, skills/)
- Implemented autonomous project activation — agent recognizes context and activates/deactivates projects without user intervention
- Built MCP server coupling where projects can declare MCP servers that spin up on activation and shut down on deactivation
- Designed single-active constraint with automatic deactivation of the current project when a new one activates

**MCP (Model Context Protocol) Integration:**
- Integrated rmcp library supporting stdio and HTTP transport for external tool servers
- Built `McpRegistry` managing server lifecycle with reference counting for safe multi-agent access
- Implemented dynamic tool discovery with cached tool definitions exposed to the agent's turn loop
- Designed graceful server lifecycle management tied to project activation/deactivation

**Notification Routing:**
- Built extensible notification system with built-in channels (agent_wake, agent_feed, inbox) and external channels (ntfy.sh push notifications, HTTP webhooks)
- Implemented per-task routing configuration — pulses and subagents declare their output channels
- Designed graceful degradation where failed external deliveries are logged but don't block other channels

**Multi-Provider LLM Abstraction:**
- Designed `ModelProvider` trait with implementations for Anthropic (Claude), OpenAI (GPT-4o, o-series), Google (Gemini), and Ollama (local models)
- Built provider failover with configurable primary and fallback chains
- Implemented `EmbeddingProvider` trait for vector embedding generation across providers
- Created model tiering system for cost-optimized task delegation

**Agent Runtime & Context Assembly:**
- Architected turn-based agent loop assembling context from: system prompt (SOUL.md), user profile (USER.md), curated memory (MEMORY.md), observation log, recent context narrative, unread inbox, active project context, and available skills/MCP tools
- Built token estimation for dynamic context window sizing
- Implemented cancellation-aware execution with `tokio::select!` for clean shutdown
- Designed tool registry spanning core (read, write, edit, exec), memory (search, inbox), project management, scheduling, and background tasks

**Encrypted Secret Storage:**
- Implemented AES-GCM-SIV encryption for local secret storage (API keys, tokens)
- Built `secret` CLI command for secure credential management
- Designed encrypted file format with authenticated encryption preventing tampering

**Daemon Lifecycle Management:**
- Built multi-command CLI: `serve` (gateway), `setup` (wizard), `logs`, `stop`, `connect`, `secret`, `update`
- Implemented PID file tracking for process management
- Designed foreground/background mode split with signal handling via `nix` crate

## Architecture & Code Quality

**Production-Scale Rust Codebase:**
- ~53,000 lines of Rust across 144 files with strict clippy pedantic enforcement
- `unsafe_code` forbidden; `unwrap_used`, `expect_used`, `panic` all denied in production code
- Full async/await with multi-threaded tokio runtime
- `Arc<RwLock<T>>` for thread-safe shared registries (MCP, projects)

**Testing Strategy:**
- 9 integration test suites (~4,000 lines) covering memory, gateway, MCP, projects, background tasks, daemon lifecycle, pulse scheduling, skills, and inbox
- Unit tests for complex modules with structured `#[expect]` annotations
- wiremock for HTTP-level mocking of external channels
- Pre-commit hooks enforce `cargo test --quiet` on every commit

**File-First Design Philosophy:**
- All state lives in human-readable files — filesystem as source of truth
- Episode storage, observations, project manifests, and configuration all inspectable and editable
- Hot reload with filesystem watching for configuration changes
- No opaque databases — SQLite and Tantivy indexes are implementation details, not primary state

**Cross-Platform Release:**
- Targets Linux x86_64, Linux aarch64, and macOS aarch64 (Apple Silicon)
- CalVer release scheme (YYYY.0M.0D) with automated CI/CD pipeline
- Platform-aware FFI handling (`std::ffi::c_char` over hardcoded types)

This project demonstrates advanced Rust systems architecture, LLM agent framework design, hybrid search implementation, multi-channel convergence, and production-quality daemon development at scale.