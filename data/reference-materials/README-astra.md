# Project Astra

> An autonomous AI productivity manager powered by Google's Agent Development Kit, Neo4j knowledge graphs, and advanced sandbox security.

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Discord](https://img.shields.io/badge/discord-bot-5865F2.svg)](https://discord.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Overview

Project Astra is a sophisticated autonomous AI assistant that manages productivity through natural conversation. Unlike traditional task management applications with AI features, Astra inverts the paradigm: **the user controls direction, the AI controls execution**. Users express what they want to accomplish, and Astra autonomously handles planning, scheduling, task triage, and adaptation.

**Core Philosophy**: Users never manually schedule, organize, or update—they just talk.

## Technical Highlights

### 🏗️ Architecture

- **Agent Framework**: Built on Google's Agent Development Kit (ADK) with unified code execution model
- **Async-First Design**: Full async/await implementation with proper event loop handling across ~4,000 lines of production Python
- **Multi-tier Architecture**: Discord bot → Session manager → Agent executor → Secure sandbox → Background scheduler
- **Knowledge Graph**: Neo4j-based long-term memory system with custom entity/relationship types via Graphiti
- **Dual Database System**: SQLite for operational data (tasks, events, jobs) + Neo4j for semantic knowledge

### 🔒 Sandbox Security (Defense-in-Depth)

**File**: [`app/execution/sandbox.py`](app/execution/sandbox.py)

Implements a sophisticated secure Python execution environment:

- **Import Blacklist**: Blocks 30+ dangerous modules (file I/O, networking, process control, code execution)
- **AST-Based Validation**: Parses code to Abstract Syntax Tree before execution, validates imports statically
- **Resource Limits**: Configurable timeouts (default 5s), output buffering (10k character limit)
- **Intelligent Error Messages**: Instead of generic errors, provides actionable suggestions:
  - `NameError` → "Try: `describe('function_name')` if it's a tool"
  - `ImportError` → Lists blocked modules and suggests alternatives
  - Database errors → Recommends schema inspection and validation
- **Async Coroutine Handling**: Automatically awaits coroutines in namespace to prevent event loop conflicts

### 🧠 Knowledge Graph Memory System

**Files**: [`app/memory/graphiti/`](app/memory/graphiti/)

Implements persistent learning using Neo4j knowledge graph:

#### Custom Type System
Defined domain-specific entities and relationships using Pydantic models:

**Entity Types**:
- `UserEntity`: Work style, timezone, occupation, availability patterns
- `TaskType`: Category, duration estimates, complexity, focus requirements
- `TimeContext`: Time of day preferences, energy levels, day-of-week patterns
- `Project`: Status, priority, deadline, domain knowledge
- `Tool`: Proficiency levels, usage frequency, purpose mapping
- `Activity`: Type, frequency, duration, preference strength

**Edge Types (Relationships)**:
- `Preference`: Strength, reasoning, context, stated vs. inferred
- `Pattern`: Learned behavior patterns from observation
- `TemporalFact`: Time-sensitive information with expiry
- `Relationship`: Entity connections with metadata

#### Progressive Context Retrieval
**File**: [`app/memory/graphiti/context_retriever.py`](app/memory/graphiti/context_retriever.py)

Uses **type-based filtering** instead of keyword matching:
```python
# Execute 4 parallel searches with different filters
preferences = graphiti.search(query, filter=SearchFilters(edge_types=["Preference"]))
patterns = graphiti.search(query, filter=SearchFilters(edge_types=["Pattern"]))
temporal = graphiti.search(query, filter=SearchFilters(edge_types=["TemporalFact"]))
general = graphiti.search(query)  # Unfiltered
```

**Progressive Disclosure Pattern**:
1. Prioritizes preferences (limit 2) over patterns (limit 3)
2. Deduplicates across categories
3. Total context limit prevents overwhelming agent
4. Graceful degradation on service failure

### 🤖 Self-Discovering Agent Architecture

**File**: [`app/agents/execution_agent.py`](app/agents/execution_agent.py)

**Unified Execution Model**: Rather than discrete tool functions, the agent has a single tool—`execute_python_code()`—maximizing flexibility:

- **Dynamic Tool Discovery**: No hardcoded tool list in system prompt
- **Exploration Interface**:
  - `help()` - Navigation instructions
  - `ls()` - Lists available tool categories (uses `pkgutil.iter_modules()`)
  - `describe('tool_name')` - Detailed documentation with signatures
- **Error-Driven Learning**: Sandbox errors guide the agent toward correct usage
- **Context Building**: Async retrieval of conversation history + Graphiti memories before execution

**Technical Pattern**: Agent explores the sandbox environment using introspection, discovers capabilities dynamically, and learns from execution feedback—no manual prompt maintenance required.

### ⏰ Background Job Scheduler

**File**: [`app/execution/scheduler.py`](app/execution/scheduler.py)

Sophisticated async background task execution system:

#### Recurrence Pattern Support
**File**: [`app/sandbox/automation/recurrence_parser.py`](app/sandbox/automation/recurrence_parser.py)

- **Simple patterns**: `daily`, `hourly`, `weekly`
- **Weekday-specific**: `weekly:mon,wed,fri`
- **Day-of-month**: `monthly:1,15`
- **Interval-based**: `interval:hours:2`, `interval:days:3`
- **Full cron syntax**: `0 9 * * *` (standard 5-field cron)

Implementation:
- Uses `dateutil.rrule` for standard patterns
- Uses `croniter` for cron expressions
- Supports recurrence end dates with automatic job completion

#### Pre-Execution Validation
When creating automated jobs:
1. **Test execution**: Code runs once in validation mode
2. **Validation flag**: `_validation_mode=True` prevents side effects
3. **Async handling**: Uses `ThreadPoolExecutor` to avoid nested event loop issues
4. **Failure prevention**: Job not created if test fails

#### Execution Pipeline
```
Database Poll (60s interval)
  ↓
Find Due Jobs (next_run_at ≤ now)
  ↓
Validate Status (active only)
  ↓
Execute in Sandbox (with timeout)
  ↓
Store Execution History
  ↓
Calculate Next Run (for recurring)
  ↓
Send Results to Discord
```

### 🧩 Tool Ecosystem (52+ Functions)

**Directory**: [`app/sandbox/`](app/sandbox/)

9 categories of tools, all dynamically discovered:

#### Tasks ([`app/sandbox/tasks/`](app/sandbox/tasks/))
- `create_task()` - Flexible date parsing (relative & absolute)
- `query_tasks()` - Advanced filtering, sorting, grouping
- `update_task()` - Partial updates with validation
- `complete_task()` - Marks complete with timing metadata
- Task dependencies (blocked_by), recurrence patterns, priority levels

#### Events ([`app/sandbox/events/`](app/sandbox/events/))
- Calendar event CRUD operations
- All-day event support
- Recurring events with parent/child hierarchy
- Cancel vs. delete (soft/hard removal)

#### Time Blocks ([`app/sandbox/time_blocks/`](app/sandbox/time_blocks/))
- Scheduled work periods with block types (`deep_work`, `routine`, `break`, `flexible`)
- `find_free_slots()` - Intelligent availability detection
- Actual vs. planned task tracking
- Duration calculation and validation

#### Dates ([`app/sandbox/dates/`](app/sandbox/dates/))
Ultra-flexible date parsing:
- Relative: `"tomorrow"`, `"next Friday"`, `"in 3 days"`
- Absolute: ISO format, written dates
- Special: `"end of month"`, `"Q4 2025"`, `"start of next week"`
- Formatting: Human-friendly relative output (`"2 days ago"`)

#### Automation ([`app/sandbox/automation/`](app/sandbox/automation/))
- `create_automated_job()` - With pre-execution validation
- `list_automated_jobs()` - Filtering and sorting
- `pause_automated_job()`, `cancel_automated_job()`
- `update_automated_job()` - Modify job configuration
- `execute_job_now()` - Manual trigger
- `get_execution_history()` - Past runs analysis
- `cleanup_execution_history()` - Archive maintenance

#### Memories ([`app/sandbox/memories/`](app/sandbox/memories/))
- `add_memory()` - Store explicit insights (insight/preference/pattern/fact)
- `search_memories()` - Type-filtered search with confidence scoring

#### Discord Utils ([`app/sandbox/discord_utils/`](app/sandbox/discord_utils/))
- `send_message()` - Text with automatic chunking
- `send_embed()` - Rich embeds with colors, fields, reactions
- `send_ephemeral()` - Interaction-only messages

#### Agent Tasks ([`app/sandbox/agent_tasks/`](app/sandbox/agent_tasks/))
Meta-operations:
- `trigger_agent_run()` - Queue message for agent processing
- `list_queued_tasks()` - View pending operations
- `cancel_queued_task()` - Remove from queue

### 🎯 Intelligent Session Management

**File**: [`app/preprocessor/session_manager.py`](app/preprocessor/session_manager.py)

Uses Cerebras LLM (llama3.1-8b) for intelligent conversation boundary detection:

- **Automatic Boundary Detection**: Analyzes conversation flow to detect natural session transitions
- **Forced Boundaries**: Timeout (60 min) or max messages (100)
- **Session Capture**: Previous session stored as Graphiti episode on boundary
- **Context Continuity**: Maintains conversation context across boundaries

**Pattern**: Balances automatic vs. manual boundaries—prevents context loss while respecting conversation flow.

### 📊 Database Architecture

**Files**: [`app/memory/sql/`](app/memory/sql/)

#### ORM Models
SQLAlchemy models with advanced features:

- `TaskModel` - Priority, status, recurrence, dependencies, time tracking
- `EventModel` - Calendar events with recurrence support
- `TimeBlockModel` - Scheduled work periods with block types
- `SkillModel` - Custom skills/functions for agent extension
- `ScheduledJobModel` - Automated jobs with retry logic
- `JobExecutionHistoryModel` - Execution tracking and analysis
- `PendingConfirmationModel` - Human-in-loop approval workflows

#### Advanced SQL Features
**File**: [`app/memory/sql/schema.sql`](app/memory/sql/schema.sql)

Uses **generated columns** for computed fields:
```sql
-- Automatically computed columns
is_overdue GENERATED ALWAYS AS (
    due_date IS NOT NULL AND due_date < CURRENT_DATE
)
days_until_due GENERATED ALWAYS AS (
    julianday(due_date) - julianday(CURRENT_DATE)
)
```

**Foreign Key Support**:
- Task dependencies (`blocked_by_task_id`)
- Parent/child relationships
- Recurring instance tracking
- Cascade deletion rules

### 🔍 Observability & Tracing

**File**: [`app/utils/logging_util.py`](app/utils/logging_util.py)

Structured logging with Phoenix OpenTelemetry integration:

- **Phoenix Tracing**: Automatic instrumentation of agent execution
- **Structured Logs**: Timestamp, level, logger name, execution times
- **Log Levels**: DEBUG (detailed flow), INFO (actions), WARNING (issues), ERROR (failures)
- **Visualization**: Phoenix UI at `http://localhost:6006`
- **ADK Instrumentation**: Traces internal agent reasoning steps

### 🔗 Discord Integration

**Files**: [`app/bot_setup/`](app/bot_setup/), [`app/discord_integration/`](app/discord_integration/)

#### Message Processing Pipeline
**File**: [`app/bot_setup/message_handler.py`](app/bot_setup/message_handler.py)

1. Check for dangerous intent
2. Send progress message with animated updates
3. Build context (history + memories)
4. Execute agent via ADK
5. Process queued Discord messages
6. Handle reactions for confirmations

#### Rich Messaging
- **Message Queue**: Agent can queue multiple messages/embeds
- **Rich Embeds**: Colored embeds with title/description, fields, footers
- **Reaction-Based Interactions**: Confirmation workflows using reactions
- **Ephemeral Messages**: Interaction-only visibility

#### Reaction Handler
**File**: [`app/bot_setup/reaction_handler.py`](app/bot_setup/reaction_handler.py)

- Tracks pending confirmations in database
- Maps reactions to approval/rejection actions
- Executes follow-up actions on confirmation
- Timeout handling for stale confirmations

### 🧪 Testing Infrastructure

**Directory**: [`tests/`](tests/)

#### Test Philosophy
- **Agent behavior**: Manual testing only (LLMs are non-deterministic)
- **Tool functionality**: Automated testing (deterministic)
- **Sandbox integration**: Verified after any sandbox changes
- **Security**: Ensures dangerous operations remain blocked

#### Test Categories

**Sandbox Tests** ([`tests/sandbox/`](tests/sandbox/)):
- `test_sandbox_tools.py` - Verifies all tools available in globals
- `test_sandbox_safety.py` - Ensures dangerous operations blocked

**Tool Tests** ([`tests/tools/`](tests/tools/)):
- `test_tasks.py` - Task CRUD operations
- `test_events.py` - Event management
- `test_dates.py` - Date parsing accuracy
- `test_time_blocks.py` - Time block operations
- `test_automation.py` - Job creation and scheduling

**Unit Tests** ([`tests/unit/`](tests/unit/)):
- `test_scheduling.py` - Job execution logic
- `test_cron_support.py` - Cron pattern parsing
- `test_cerebras_client.py` - Session boundary detection

## Technical Stack

| Component | Technology |
|-----------|-----------|
| **Agent Framework** | Google Agent Development Kit (ADK) |
| **Language** | Python 3.11+ (full async/await) |
| **Knowledge Graph** | Neo4j + Graphiti |
| **Operational Database** | SQLite with SQLAlchemy ORM |
| **LLM Providers** | Google Gemini (agent reasoning), Cerebras (session detection) |
| **Integration** | Discord.py (bot framework) |
| **Observability** | Phoenix OpenTelemetry tracing |
| **Scheduling** | APScheduler patterns + custom async poller |
| **Date Parsing** | python-dateutil, croniter |

## Project Structure

```
project-astra/
├── app/
│   ├── agents/               # Agent executor (Google ADK)
│   ├── bot_setup/            # Discord bot lifecycle
│   ├── discord_integration/  # Rich messaging, reactions
│   ├── execution/            # Sandbox + scheduler
│   ├── memory/               # Graphiti + SQLite
│   │   ├── graphiti/         # Knowledge graph operations
│   │   └── sql/              # Relational database
│   ├── preprocessor/         # Session management
│   ├── sandbox/              # 52+ tool functions (9 categories)
│   │   ├── agent_tasks/      # Meta-operations
│   │   ├── automation/       # Job scheduling
│   │   ├── dates/            # Date parsing/formatting
│   │   ├── discord_utils/    # Messaging
│   │   ├── events/           # Calendar events
│   │   ├── memories/         # Knowledge graph access
│   │   ├── skills/           # Custom skills
│   │   ├── tasks/            # Task management
│   │   └── time_blocks/      # Work period scheduling
│   └── utils/                # Logging, text chunking
├── tests/                    # Sandbox, tool, and unit tests
├── docs/                     # Development guidelines
└── scripts/                  # Maintenance utilities
```

## Key Technical Achievements

1. **Unified Code Execution Model**: Agent writes Python for any task, maximizing flexibility without discrete tool APIs
2. **Self-Discovering Sandbox**: No hardcoded tool lists—dynamic discovery via `ls()` and `describe()`
3. **Knowledge Graph with Type Filtering**: Semantic filtering using custom entity/relationship types, not keyword matching
4. **Intelligent Session Detection**: LLM-based conversation boundary detection, not just timeouts
5. **Defense-in-Depth Sandbox**: AST validation + import blacklist + resource limits + intelligent errors
6. **Sophisticated Job Scheduling**: Pre-execution validation, multiple recurrence patterns (including cron), execution history
7. **Progressive Context Disclosure**: Carefully prioritized information injection with graceful degradation
8. **Flexible Date Parsing**: Natural language dates (relative and absolute) with complex pattern support
9. **Rich Discord Integration**: Message queuing, embeds, reaction-based confirmations, asynchronous processing
10. **Full Observability**: Phoenix OTEL tracing of entire agent execution flow including ADK internals

## Code Metrics

- **Production Code**: ~4,000 lines
- **Tool Functions**: 52+ across 9 categories
- **Database Models**: 10+ ORM models
- **Test Modules**: 8+ test files
- **Integration Points**: 4 major external services (Google, Neo4j, Cerebras, Discord)

## Design Patterns & Best Practices

### Async/Event Loop Architecture
- Full async/await implementation throughout
- Proper event loop handling for nested async operations
- Automatic coroutine awaiting in sandbox namespace

### Dynamic Module Discovery
```python
# No hardcoded lists—discover at runtime
for importer, module_name, is_pkg in pkgutil.iter_modules(sandbox_path):
    module = importlib.import_module(f'app.sandbox.{module_name}')
    # Extract docs, functions, signatures dynamically
```

### Progressive Disclosure Pattern
```python
# Prioritize important information
1. Preferences (2 max)
2. Patterns (3 max)
3. Temporal facts (remaining slots)
4. General context (remaining slots)
# Total limit prevents context overload
```

### Graceful Degradation
```python
try:
    memories = await get_relevant_context(...)
except (ConnectionError, TimeoutError):
    logger.warning("Context service unavailable")
    # Continue with empty context—system still functional
```

### Error-Driven Learning
Sandbox executor provides actionable error messages:
- Suggests next steps (`describe()`, `help()`)
- Explains why operations are blocked
- Helps agent self-correct without human intervention

## Development Philosophy

From [`CLAUDE.md`](CLAUDE.md):

- **Scope Control**: Implement only what's requested—no feature creep
- **Incremental Changes**: Small, focused changes over large refactors
- **Maintainability First**: Self-documenting code, comments only for "why"
- **Robust Over Fragile**: Prefer existing libraries or LLM calls over regex/heuristics
- **Test Critical Paths**: Sandbox and tool changes must be tested before commit
- **Breaking Changes OK**: No backwards compatibility burden—move fast

## Setup & Configuration

### Prerequisites
- Python 3.11+
- Neo4j instance (for Graphiti)
- Discord bot token
- Google API key (Gemini)
- Cerebras API key

### Installation
```bash
# Clone repository
git clone https://github.com/yourusername/project-astra.git
cd project-astra

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and configuration

# Initialize databases
python scripts/clean_databases.py  # First-time setup

# Run tests
pytest tests/

# Start bot
python -m app.main
```

### Environment Variables
```bash
DISCORD_TOKEN=your_discord_bot_token
GEMINI_API_KEY=your_google_api_key
CEREBRAS_API_KEY=your_cerebras_api_key
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
```

## Usage

Once running, interact with the bot in Discord:

```
User: Schedule time to work on the presentation tomorrow morning

Bot: I've created a deep work block from 9:00 AM to 11:00 AM tomorrow for
     "Presentation work". I also created a task "Complete presentation" due
     tomorrow evening. Would you like me to set up a reminder 30 minutes before?

User: Yes, and make sure I have coffee scheduled before that

Bot: Added a 15-minute routine block at 8:45 AM for "Coffee preparation".
     I've also set a daily recurring task to ensure coffee supplies are stocked.
```

The agent:
- Parsed relative dates ("tomorrow morning")
- Created appropriate time blocks with correct types
- Linked tasks to time blocks
- Inferred additional needs (reminder, supplies)
- Proposed proactive automation

## Performance Characteristics

- **Agent Response Time**: 2-5 seconds (typical)
- **Sandbox Execution**: <500ms (most operations), 5s timeout max
- **Memory Retrieval**: <1s (parallel searches)
- **Session Detection**: <2s (Cerebras inference)
- **Background Job Polling**: 60s interval (configurable)
- **Database Queries**: <100ms (indexed queries)

## Future Enhancements

See [`TODO.md`](TODO.md) for active development roadmap.

## License

MIT License - See [`LICENSE`](LICENSE) for details

## Contributing

This is a portfolio/resume project. If you find it interesting and want to discuss the architecture or implementation, feel free to reach out!

## Acknowledgments

Built with:
- [Google Agent Development Kit](https://github.com/google/agent-dev-kit)
- [Graphiti](https://github.com/getzep/graphiti) - Knowledge graph framework
- [Discord.py](https://discordpy.readthedocs.io/) - Discord API wrapper
- [Phoenix](https://phoenix.arize.com/) - LLM observability

---

**Project Astra** - Where autonomous AI meets productivity management
