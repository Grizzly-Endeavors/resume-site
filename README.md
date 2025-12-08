# AI-Powered Interactive Resume Platform

An intelligent, conversational resume platform that dynamically generates personalized content based on visitor interests using RAG (Retrieval-Augmented Generation) and dual-LLM architecture.

## Overview

This platform replaces traditional static resumes with an AI-driven conversational interface. Visitors chat with an AI assistant that understands their interests and role, then generates customized HTML sections highlighting relevant experience from a PostgreSQL database with pgvector embeddings. The system uses semantic search to surface the most relevant experiences and dynamically assembles content tailored to each visitor's needs.

**Live Site:** [bearflinn.com](https://bearflinn.com)

## Technical Architecture

### Backend Stack
- **FastAPI** - Async web framework with automatic OpenAPI documentation
- **PostgreSQL 16 + pgvector** - Vector database for semantic search with 768-dimensional embeddings
- **asyncpg** - High-performance async PostgreSQL driver with connection pooling
- **Multi-Model LLM Strategy:**
  - **Primary Models (Cerebras):**
    - **Llama 3.1 8B** - Fast operations (summaries, structured output)
    - **Qwen 3 32B** - Balanced quality/speed for medium tasks
    - **Qwen 3 235B** - High-quality generation (chat, HTML blocks)
  - **Fallback Models (Google Gemini):**
    - **Gemini Flash Lite** - Fallback for small/medium tasks
    - **Gemini Flash** - Fallback for large tasks with structured output support
  - **Task-Specific Selection:**
    - Chat onboarding: `ModelSize.LARGE` (Qwen 3 235B) for conversational quality
    - HTML block generation: `ModelSize.LARGE` (Qwen 3 235B) for creative content
    - Block summaries: `ModelSize.SMALL` (Llama 3.1 8B) for speed
    - Button suggestions: `ModelSize.SMALL` (Llama 3.1 8B) with structured output

### Frontend Stack
- **Vanilla JavaScript** - Zero framework overhead with modern DOM manipulation
- **CSS3** - Custom animations, responsive design, and dark mode theming
- **Dynamic HTML Generation** - Server-rendered content blocks injected with smooth transitions

### Database Schema
```sql
CREATE TABLE experiences (
    id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    skills TEXT[],
    metadata JSONB,
    embedding vector(768),
    source_file TEXT,
    content_hash TEXT,
    last_updated TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE
);
```

## Key Features

### 1. Conversational Onboarding
- Initial chat interface gathers visitor context (role, interests, specific needs)
- Adaptive prompting with turn-based hints to guide natural conversation
- XML tag parsing to detect conversation completion
- Visitor summary extraction for personalized content generation

### 2. Semantic Search with RAG
- pgvector cosine similarity search finds relevant experiences
- Context-aware deduplication tracks shown experiences to maintain variety
- Embedding generation via Google Gemini `text-embedding-004` model
- Incremental seeding system with MD5 hash tracking for automatic updates

### 3. Dynamic Content Generation
- **Block Generation:** Creates custom HTML sections with inline styling and optional JavaScript
- **Smart Prompt Engineering:** Combines visitor summary, RAG results, and previous block summaries
- **Suggested Actions:** Generates context-aware follow-up prompts based on available experiences
- **Content Compression:** Tracks shown experiences and block summaries to prevent repetition

### 4. Incremental Data Seeding
- Automatic discovery of markdown files in `data/jobs/` and `data/projects/`
- Content hash tracking prevents redundant embedding generation
- Graceful updates for changed files and additions of new content
- Structured markdown parsing extracts titles, skills, dates, and metadata

### 5. Production-Ready Infrastructure
- **Docker Compose** orchestration with multi-stage builds
- **Health checks** and database connectivity validation
- **Connection pooling** (1-10 connections) for efficient resource usage
- **Automatic migrations** run on container startup
- **Environment-based configuration** via dotenv

## Project Structure

```
resume-site/
├── backend/
│   ├── main.py              # FastAPI application entry point
│   ├── db.py                # Database pool management & schema
│   ├── seed.py              # Incremental seeding logic
│   ├── rag.py               # Vector search & RAG formatting
│   ├── models.py            # Pydantic request/response models
│   ├── ai/
│   │   ├── llm.py          # Dual-LLM handler with fallback
│   │   ├── generation.py   # Generation logic for chat/blocks/buttons
│   │   └── prompts.py      # Prompt templates
│   └── requirements.txt
├── frontend/
│   ├── index.html          # Single-page application shell
│   ├── app.js              # Client-side logic & API calls
│   └── style.css           # Responsive styling & animations
├── data/
│   ├── jobs/               # Professional experience markdown files
│   └── projects/           # Technical project markdown files
├── docker-compose.yml      # Service orchestration
└── .github/workflows/
    └── deploy.yml          # CI/CD automation
```

## API Endpoints

### `POST /api/chat`
Handles conversational onboarding phase.
- **Input:** `{message: string, history: Array<{role, content}>}`
- **Output:** `{ready: bool, visitor_summary?: string, message?: string}`

### `POST /api/generate-block`
Generates personalized HTML content blocks.
- **Input:** `{visitor_summary: string, action_type: string, action_value: string, context: CompressedContext}`
- **Output:** `{html: string, block_summary: string, experience_ids: string[]}`

### `POST /api/generate-buttons`
Creates context-aware suggested prompts.
- **Input:** `{visitor_summary: string, chat_history: Array, context: CompressedContext}`
- **Output:** `{buttons: Array<{label: string, prompt: string}>}`

## Setup & Development

### Prerequisites
- Docker & Docker Compose
- Python 3.12+
- PostgreSQL 16 with pgvector extension
- API keys for Cerebras and Google Gemini

### Environment Variables
```env
DATABASE_URL=postgresql://user:password@db:5432/resume
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=resume
CEREBRAS_API_KEY=your_cerebras_key
GEMINI_API_KEY=your_gemini_key
```

### Local Development
```bash
# Start services
docker compose up --build

# Run tests
cd backend
source venv/bin/activate
pytest

# Access application
curl http://localhost:8000/api/health
```

### Embedding Generation
- **Google Gemini text-embedding-004** - 768-dimensional embeddings for semantic search
- **Task-Type Optimization:** `retrieval_document` for stored content, `retrieval_query` for searches
- **Async Generation:** Non-blocking embedding creation during seeding

## Technical Highlights

### Multi-Model LLM Architecture
- **Three-Tier Model Strategy:**
  - `ModelSize.SMALL`: Llama 3.1 8B (primary) / Gemini Flash Lite (fallback) - Fast operations
  - `ModelSize.MEDIUM`: Qwen 3 32B (primary) / Gemini Flash Lite (fallback) - Balanced tasks
  - `ModelSize.LARGE`: Qwen 3 235B (primary) / Gemini Flash (fallback) - High-quality generation
- **Automatic Failover:** 3 retries with exponential backoff per provider before fallback
- **Task-Optimized Selection:**
  - Chat responses: LARGE model for natural, engaging conversation
  - HTML generation: LARGE model for creative, well-structured content
  - Button suggestions: SMALL model with structured output (JSON schema validation)
  - Block summaries: SMALL model for fast, concise descriptions
- **Structured Output Support:** Both Cerebras (OpenAI-compatible json_schema) and Gemini (native response_schema) for reliable JSON generation

### Vector Search Implementation
- **Cosine Similarity:** `1 - (embedding <=> query_embedding)` for relevance scoring
- **Context-Aware Ranking:** Penalizes recently shown experiences to maintain variety
- **Top-K Retrieval:** Configurable result limit (default 5) with score thresholds
- **Efficient Indexing:** HNSW indexes for sub-linear search time (commented for high-dimension compatibility)

### Prompt Engineering
- **System Prompts:** Separate templates for chat, block generation, button suggestions, and summaries
- **Context Injection:** Dynamic insertion of visitor summary, RAG results, and conversation history
- **Turn-Based Hints:** Adaptive prompting based on conversation length to ensure completion
- **Structured Extraction:** XML tag parsing and JSON schema validation for reliable outputs

### Frontend State Management
- **Context Tracker:** Maintains shown experience counts and block summaries
- **Block Data Map:** Maps DOM elements to generation metadata for regeneration
- **Chat History:** Stores conversation for context continuity
- **Smooth Animations:** CSS transitions for loading indicators, content blocks, and UI elements

## Performance Considerations

- **Connection Pooling:** asyncpg pool (1-10 connections) reduces connection overhead
- **Async Operations:** FastAPI + asyncpg enable high concurrency without threading
- **Embedding Caching:** Hash-based tracking prevents redundant embedding generation
- **Incremental Updates:** Only processes changed files during seeding
- **Lightweight Frontend:** No framework dependencies, minimal JavaScript bundle

## Security & Best Practices

- **Environment Variables:** No hardcoded credentials in codebase
- **Input Validation:** Pydantic models enforce request/response schemas
- **Database Parameterization:** asyncpg prevents SQL injection
- **Error Handling:** Graceful fallbacks with user-friendly error messages
- **CORS Configuration:** Controlled access (configured via FastAPI middleware if needed)

## Future Enhancements

- HNSW index enablement for faster vector search at scale
- Real-time streaming responses for improved perceived performance
- Analytics tracking for visitor interaction patterns
- A/B testing framework for prompt optimization
- Multi-language support with internationalization
- Export functionality (PDF resume generation from visitor session)

## License

This project is proprietary and maintained by Bear Flinn.

## Contact

For questions or collaboration opportunities, visit [bearflinn.com](https://bearflinn.com) or connect via the platform's chat interface.