# AI-Powered Interactive Resume Platform
**Dates:** December 2025 - Ongoing
**Skills:** Python, FastAPI, PostgreSQL, pgvector, RAG, Docker, JavaScript, asyncpg, Google Gemini, Cerebras, Vector Embeddings, Semantic Search, Pydantic, asyncio, CSS3

Intelligent conversational resume platform using RAG and dual-LLM architecture to dynamically generate personalized content based on visitor interests. Features semantic search with pgvector, context-aware content generation, and incremental data seeding. Deployed with Docker Compose on self-hosted infrastructure. Available at resume.bearflinn.com.

Repo: https://github.com/Grizzly-Endeavors/resume-site

## Technical Achievements

**RAG-Powered Semantic Search:**
- Implemented pgvector extension with 768-dimensional embeddings for experience retrieval
- Built cosine similarity search with context-aware ranking penalizing recently shown content
- Integrated Google Gemini text-embedding-004 model for semantic vector generation
- Designed top-k retrieval system (configurable limit, default 5) with relevance scoring
- Created efficient query pipeline combining vector search with metadata filtering

**Multi-Model LLM Architecture with Intelligent Fallback:**
- Architected three-tier model strategy across six models (3 Cerebras primary + 3 Gemini fallback)
- Configured task-optimized model selection: Llama 3.1 8B (speed), Qwen 3 32B (balanced), Qwen 3 235B (quality)
- Implemented automatic failover with 3 retries per provider using exponential backoff (1s, 2s, 4s)
- Built strategic model routing: LARGE for chat/blocks (quality), SMALL for summaries/buttons (speed)
- Designed dual structured output systems: OpenAI-compatible json_schema (Cerebras) and native response_schema (Gemini)
- Created think-tag filtering removing reasoning tokens from Qwen model outputs
- Implemented temperature tuning: 0.0 for deterministic structured output, 0.7 for creative generation

**Conversational Onboarding System:**
- Developed multi-turn chat interface gathering visitor role, interests, and specific needs
- Implemented adaptive prompting with turn-based hints (force completion after 5 turns)
- Built XML tag parsing for visitor summary extraction from LLM responses
- Created conversation state management tracking user/assistant turns
- Designed seamless transition from chat to personalized content generation

**Dynamic Content Generation Pipeline:**
- Built HTML block generation with inline styling, semantic markup, and optional JavaScript
- Engineered prompt templates combining visitor summary, RAG results, and previous block summaries
- Implemented context compression tracking shown experience IDs and block summaries
- Created suggested action system generating context-aware follow-up prompts
- Designed variety enforcement preventing repetition across multiple generated sections

**Incremental Data Seeding System:**
- Developed automatic markdown file discovery from data/jobs and data/projects directories
- Implemented MD5 hash-based change detection for smart incremental updates
- Built structured parsing extracting titles, skills, dates, and metadata from markdown
- Created upsert logic handling new insertions and updates for existing experiences
- Designed graceful startup allowing app to continue with existing data on seed failures

**FastAPI Backend Architecture:**
- Built 3 core endpoints: /api/chat, /api/generate-block, /api/generate-buttons
- Implemented Pydantic models for request validation and response serialization
- Configured async lifespan events for database initialization and graceful shutdown
- Designed static file serving for single-page application frontend
- Created comprehensive error handling with structured logging

**PostgreSQL Database Design:**
- Designed experiences table with UUID primary keys, vector embeddings, and JSONB metadata
- Configured pgvector extension for vector similarity operations
- Built indexes on source_file and content_hash columns for efficient incremental seeding
- Implemented TIMESTAMP WITH TIME ZONE for created_at and last_updated tracking
- Designed TEXT[] skills array for multi-tag filtering

**Connection Pool Management:**
- Implemented asyncpg connection pool with configurable min (1) and max (10) connections
- Built global pool singleton pattern with lazy initialization
- Designed graceful shutdown logic closing pool on application termination
- Configured DSN-based connection string from environment variables
- Optimized for async operations with FastAPI's event loop integration

**Prompt Engineering & Context Management:**
- Developed 4 specialized prompt templates: chat, block generation, buttons, summaries
- Engineered system instructions with dynamic context injection (visitor summary, RAG results)
- Built turn-based hints adding urgency instructions after 2+ conversation turns
- Designed structured output extraction (XML tags for summaries, JSON for button lists)
- Implemented block summary generation for context tracking across multiple generations

**Frontend State Management:**
- Built vanilla JavaScript application with zero framework dependencies
- Implemented context tracker maintaining shown experience counts and block summaries
- Designed block data map linking DOM elements to generation metadata
- Created smooth loading animations with CSS transitions and scroll-into-view behavior
- Developed suggested buttons interface with dynamic prompt injection

**Docker-Based Deployment:**
- Created multi-stage Dockerfile optimizing Python dependency installation
- Configured Docker Compose orchestrating app and pgvector/pgvector:pg16 services
- Implemented health checks and depends_on for proper startup ordering
- Built environment-based configuration with dotenv integration
- Designed volume persistence for PostgreSQL data across container restarts

**CI/CD Pipeline:**
- Configured GitHub Actions workflow for automated deployments
- Built self-hosted runner integration for push-to-deploy workflow
- Implemented automatic database migrations and seed execution on startup
- Designed zero-downtime deployment with health check validation

**Markdown Parsing & Metadata Extraction:**
- Built regex-based parser extracting titles (first H1), skills, and dates from markdown
- Implemented type detection based on source folder (jobs vs projects)
- Designed JSONB metadata storage for flexible schema evolution
- Created content body extraction preserving markdown formatting
- Built skills array parsing splitting comma-separated values

**Vector Similarity Operations:**
- Implemented cosine distance queries using pgvector's <=> operator
- Built relevance scoring formula: `1 - (embedding <=> query_embedding)`
- Designed ORDER BY distance ASC with LIMIT for top-k retrieval
- Created context-aware penalty system reducing scores for recently shown experiences
- Configured threshold-based filtering for minimum relevance scores

**Error Handling & Resilience:**
- Implemented try/catch blocks with graceful fallbacks on LLM failures
- Built structured logging with Python's logging module for debugging
- Designed fallback button responses on generation errors
- Created startup resilience allowing app to run with existing data on seed failures
- Implemented HTTP exception handling with proper status codes

## Architecture & Code Quality

**Async/Await Patterns:**
- Full async implementation using FastAPI, asyncpg, and httpx
- No blocking I/O operations in request handlers
- Proper async context managers for database connections
- Concurrent request handling via ASGI server (Uvicorn)

**Type Safety & Validation:**
- Pydantic models for all API request/response schemas
- Type hints throughout Python codebase
- Runtime validation preventing invalid data from reaching business logic
- Clear error messages for validation failures

**Separation of Concerns:**
- Distinct modules: main.py (routing), db.py (data layer), ai/ (generation logic), rag.py (search)
- Prompt templates isolated in ai/prompts.py
- Models defined separately in models.py
- Clear boundaries between API, business logic, and data access layers

**Development Practices:**
- pytest configuration with pytest-asyncio for async test support
- Environment-based configuration (dev/prod)
- Requirements.txt for reproducible dependency management
- Comprehensive logging for debugging and monitoring

This project demonstrates modern full-stack development with AI/ML integration, vector database operations, dual-LLM orchestration, and production deployment with Docker. Highlights advanced prompt engineering, RAG implementation, and async Python patterns.
