# Project Astra (Autonomous AI Productivity Manager)
**Dates:** Ongoing
**Skills:** Python, Google Agent Development Kit (ADK), Neo4j, SQLite, Discord.py, Async/Await, Knowledge Graphs, Secure Code Execution, OpenTelemetry, System Architecture Design

An autonomous AI assistant managing productivity through natural conversation, built on Google's Agent Development Kit with Neo4j knowledge graphs and advanced sandbox security. Unlike traditional task management apps with AI features, Astra inverts the paradigm: users control direction while the AI controls execution autonomously handling planning, scheduling, task triage, and adaptation.

## Technical Achievements

**Agent Framework & Architecture:**
- Built unified agent framework on Google's Agent Development Kit with ~4,000 lines of production Python
- Implemented full async/await design with proper event loop handling throughout entire codebase
- Architected multi-tier system: Discord bot → Session manager → Agent executor → Secure sandbox → Background scheduler
- Developed self-discovering agent architecture with dynamic tool discovery using pkgutil.iter_modules() and runtime introspection
- Designed unified execution model where agent writes Python for any task, maximizing flexibility without discrete tool APIs

**Knowledge Graph Memory System:**
- Implemented Neo4j-based long-term memory using Graphiti knowledge graph framework
- Designed dual database system: SQLite for operational data (tasks, events, jobs) + Neo4j for semantic knowledge
- Created custom type system with domain-specific entities (UserEntity, TaskType, TimeContext, Project, Tool, Activity) and edge types (Preference, Pattern, TemporalFact, Relationship)
- Built progressive context retrieval using type-based filtering instead of keyword matching with 4 parallel searches
- Implemented progressive disclosure pattern prioritizing preferences over patterns with total context limits preventing agent overload

**Sandbox Security (Defense-in-Depth):**
- Engineered secure Python execution environment with AST-based validation parsing code before execution
- Implemented import blacklist blocking 30+ dangerous modules (file I/O, networking, process control, code execution)
- Configured resource limits with timeouts (default 5s) and output buffering (10k character limit)
- Developed intelligent error messaging system providing actionable suggestions instead of generic errors
- Built automatic coroutine handling to prevent event loop conflicts in async namespace

**Background Job Scheduler:**
- Developed sophisticated async background task execution system with 60-second polling interval
- Implemented comprehensive recurrence pattern support: simple patterns (daily, hourly, weekly), weekday-specific (weekly:mon,wed,fri), day-of-month (monthly:1,15), interval-based (interval:hours:2), and full cron syntax (0 9 * * *)
- Created pre-execution validation testing code once in validation mode before scheduling
- Built execution pipeline: Database poll → Find due jobs → Validate status → Execute in sandbox → Store history → Calculate next run → Send Discord results
- Designed retry logic and failure handling for automated jobs

**Tool Ecosystem (52+ Functions):**
- Built 9 categories of dynamically-discoverable tools spanning tasks, events, time blocks, dates, automation, memories, Discord utils, and agent tasks
- Implemented ultra-flexible date parsing supporting relative (tomorrow, next Friday, in 3 days), absolute (ISO format, written dates), and special formats (end of month, Q4 2025)
- Created task management system with flexible date parsing, dependencies (blocked_by), recurrence patterns, and priority levels
- Developed time block scheduling with block types (deep_work, routine, break, flexible) and intelligent availability detection

**Intelligent Session Management:**
- Implemented LLM-based (Cerebras llama3.1-8b) conversation boundary detection analyzing flow for natural transitions
- Configured forced boundaries at timeout (60 min) or max messages (100)
- Designed session capture storing previous session as Graphiti episode on boundary
- Maintained context continuity across session boundaries

**Database Architecture:**
- Created SQLAlchemy ORM models with advanced features: TaskModel, EventModel, TimeBlockModel, SkillModel, ScheduledJobModel, JobExecutionHistoryModel, PendingConfirmationModel
- Implemented SQL generated columns for computed fields (is_overdue, days_until_due)
- Designed foreign key relationships for task dependencies, parent/child relationships, and recurring instance tracking
- Configured cascade deletion rules and proper referential integrity

**Discord Integration:**
- Built 600+ line Discord integration with singleton client pattern preventing multiple instances
- Implemented rich messaging queue with embeds, colored embeds, fields, footers, and reactions
- Developed 6 notification types: VOD requests, review completion, booking confirmations, 24-hour reminders, 30-minute reminders (user and admin)
- Created reaction-based interaction system with confirmation workflows and timeout handling
- Enabled automatic guild enrollment during OAuth flow

**Observability & Tracing:**
- Integrated Phoenix OpenTelemetry for automatic agent execution instrumentation
- Implemented structured logging with timestamp, level, logger name, and execution times
- Configured Phoenix UI visualization for debugging agent reasoning steps
- Added ADK internal tracing capabilities for deep system introspection

## Key Design Patterns

**Dynamic Module Discovery:**
No hardcoded tool lists—runtime discovery via pkgutil scanning sandbox packages and extracting docs, functions, and signatures dynamically

**Progressive Disclosure Pattern:**
Carefully prioritized information injection: Preferences (2 max) → Patterns (3 max) → Temporal facts → General context with total limits

**Graceful Degradation:**
Services continue functioning with empty context when Graphiti unavailable, preventing total system failure

**Error-Driven Learning:**
Sandbox provides actionable error messages suggesting next steps (describe(), help()) enabling agent self-correction without human intervention

## Architecture & Code Quality

**Production-Quality Codebase:**
- ~4,000 lines of production Python with full type hints throughout
- 52+ tool functions across 9 categories
- 10+ SQLAlchemy ORM models
- 8+ test modules covering sandbox, tools, and units
- 4 major external service integrations (Google ADK, Neo4j, Cerebras, Discord)

**Development Philosophy:**
Scope control (implement only what's requested), incremental changes, maintainability-first code, robust libraries over fragile regex/heuristics, test critical paths, and no backwards compatibility burden for rapid iteration

This project demonstrates advanced system architecture, secure code execution, knowledge graph integration, and autonomous agent development at production scale.