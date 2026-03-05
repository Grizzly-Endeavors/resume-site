# Ursix (Semantic Linter)
**Dates:** Ongoing
**Skills:** Rust, Async/Await, Tokio, LLM Integration, CLI Design, JSON Schema, Token-Aware Chunking, Exponential Backoff, CI/CD Pipelines, Unix Philosophy, Structured Output, YAML Configuration

A semantic linting CLI tool built in Rust that catches issues traditional linters can't: vague naming, poor error messages, missing edge cases, hardcoded secrets. Unlike chat-based AI review tools, Ursix is designed for automation — always-valid JSON output, meaningful exit codes, stdin/stdout composability, and stateless execution. Supports Ollama, Google Gemini, and any OpenAI-compatible API.

Repo: https://github.com/Grizzly-Endeavors/ursix

## Technical Achievements

**Multi-Provider LLM Client Abstraction:**
- Designed unified async `LlmClient` trait with implementations for Ollama, OpenAI-compatible APIs, and Google Gemini
- Built shared HTTP client with connection pooling for efficient provider communication
- Implemented structured `ChatOptions` enabling JSON mode enforcement at the API level
- Created provider-agnostic message types (`Message`, `Role`, `ToolCall`) for consistent internal representation
- Configured layered provider resolution: CLI flags > environment variables > project config > global config

**Token-Aware Parallel Chunking System:**
- Engineered file-boundary-aware splitting for git diffs preserving complete file context within each chunk
- Implemented configurable concurrency (default 4 parallel chunks) with tokio task spawning
- Built token limit checking with three-level response system (Ok/Warning/Error) using configurable thresholds
- Designed dual tokenizer strategy: fast heuristic mode (~4 chars/token) and accurate GPT-2 tokenizer via HuggingFace (lazy-loaded with `OnceLock`)
- Created dry-run mode showing token estimates and chunking plans before committing to API calls

**Intelligent Retry Logic with Exponential Backoff:**
- Implemented configurable retry system with jitter (plus/minus 25%) preventing thundering herd on rate limits
- Built intelligent error classification distinguishing retryable errors (rate limits, network, timeouts) from permanent failures (auth, parse)
- Configured defaults: 3 max retries, 500ms initial delay, 30s max delay, 2.0x multiplier
- Integrated `is_retryable()` trait method on LLM error types for provider-specific retry decisions

**LLM JSON Output Repair:**
- Built 1,100-line repair module handling common LLM output failures: markdown fences, Python booleans, single quotes, trailing commas, Python None literals
- Implemented safety-ordered repair pipeline: extraction, normalization, then structural fixing
- Designed `RepairKind` enum tracking all applied transformations for diagnostic reporting
- Created automatic truncation detection with context reporting for partial LLM responses

**Semantic Rule System:**
- Designed YAML-based rule configuration organized by category (security, style, performance) with severity levels (Error, Warning, Info)
- Implemented file glob patterns for rule applicability scoping (e.g., `"*.rs"` rules only apply to Rust files)
- Built layered rule resolution: project rules extend global rules per-category with case-insensitive filtering
- Created rule locations with precedence: `.ursix/rules.yml` > project root > `~/.config/ursix/rules.yml`

**Stateless Pipeline Execution Model:**
- Architected single-pass executor combining system prompt, input context, and user request with no message history or tool loops
- Built `PipelineError` type converting domain errors to meaningful CLI exit codes (0-4 range)
- Implemented `Arc<str>`-based `InputContext` for zero-copy content sharing across async tasks
- Designed pipeline integration with retry logic, structured logging, and partial result support

**Five Command Architecture:**
- `review`: Semantic linting against rules.yml with chunked parallel processing and CI-ready exit codes
- `derive`: Text transformation (explanation, commit-msg, summary) with chunked synthesis for large inputs
- `fix`: Code transformation in atomic (single issue) or whole-file mode with unified diff output
- `status`: Pre-flight provider connectivity validation with verbose diagnostics
- `config`: Configuration introspection and debugging

**Structured Output Guarantee:**
- Enforced always-valid JSON output with documented schema — success or failure, never malformed
- Built `_meta` field on all responses with schema version, model used, and duration
- Implemented partial results support via `partial_results` field for graceful chunk failure handling
- Designed meaningful exit code semantics: 0 (success), 1 (issues found), 2 (user error), 3 (transient), 4 (permanent)

**CI/CD Integration:**
- Built for composability with Unix tools: pipe to `jq`, `xargs`, `patch`
- Created GitHub Actions workflow examples for pull request review automation
- Designed pre-commit hook integration for security-focused staged change review
- Implemented `--dry-run` flag across all commands for cost estimation before API calls

## Architecture & Code Quality

**Strict Rust Quality Standards:**
- ~15,000 lines of production Rust with clippy pedantic enforcement
- `unsafe_code` forbidden; `unwrap_used`, `expect_used`, `panic`, `todo` all denied in production code
- Full type safety with `thiserror` domain-specific error types and `anyhow` context propagation
- Structured `tracing` logging with named fields at five severity levels

**Testing Strategy:**
- Integration tests using `assert_cmd` and `predicates` for CLI behavior validation
- Mock LLM clients with atomic operation counters for call count verification
- Snapshot testing via `insta` for output format regression detection
- Timing assertions with tolerance for backoff behavior validation
- `wiremock` for HTTP-level provider mocking

**Design Philosophy:**
- No magic: explicit opt-in for all features (chunking, rules, retry)
- Automation-first: every design decision asks "Does this work in CI?"
- Composable primitives that work with standard Unix tools
- Contract-based I/O with predictable, documented behavior

This project demonstrates advanced Rust CLI development, LLM integration patterns, CI/CD-native tool design, and production-quality error handling for automation pipelines.