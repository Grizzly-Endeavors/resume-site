# AI-Powered Dynamic Resume Site — Implementation Plan

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Cloudflare Tunnel                        │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Docker Compose Stack                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐   │
│  │   FastAPI App    │  │  Postgres + PG   │  │  Cloudflared │   │
│  │   (Port 8000)    │◄─┤     Vector       │  │   Container  │   │
│  │                  │  │   (Port 5432)    │  │              │   │
│  └────────┬─────────┘  └──────────────────┘  └──────────────┘   │
└───────────│─────────────────────────────────────────────────────┘
            │
            ▼
    ┌───────────────┐
    │   Cerebras    │ ◄── Primary (speed)
    │   Gemini      │ ◄── Fallback (reliability)
    └───────────────┘
```

---

## Component Breakdown

### 1. Database Layer (Postgres + pgvector)

**Purpose:** Store resume chunks with vector embeddings for semantic search.

**Schema:**
```
experiences
├── id (UUID)
├── title (text)              -- "Senior Engineer at Acme"
├── content (text)            -- Full markdown block
├── skills (text[])           -- ["Python", "Docker", "ML"]
├── metadata (jsonb)          -- dates, links, category
└── embedding (vector(1536))  -- or 384 depending on model
```

**Implementation requirements:**
- Use `pgvector` extension for similarity search
- Seed script to parse markdown, generate embeddings, insert rows
- Simple cosine similarity query for RAG retrieval (top 3-5 results)

**Expected outcome:** Sub-100ms retrieval for 16 documents.

---

### 2. Backend (FastAPI + Python)

**Why FastAPI:** Async-native, fast iteration, good LLM library support, automatic OpenAPI docs.

**Endpoints:**

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Serve static frontend |
| `/api/chat` | POST | Initial chat to gather visitor context |
| `/api/generate-block` | POST | Generate new HTML block via RAG + LLM |
| `/api/health` | GET | Health check for monitoring |

**Core modules:**

```
backend/
├── main.py              -- FastAPI app, routes
├── llm.py               -- Cerebras/Gemini client with fallback logic
├── rag.py               -- Embedding generation + pgvector queries
├── prompts.py           -- System prompts, block generation templates
├── models.py            -- Pydantic schemas
└── db.py                -- Async postgres connection pool
```

**LLM fallback logic:**
```python
async def generate(prompt, context):
    try:
        return await cerebras_call(prompt, context, timeout=10)
    except (Timeout, APIError):
        return await gemini_call(prompt, context, timeout=30)
```

**Implementation requirements:**
- Use `httpx` for async LLM API calls
- Use `asyncpg` for database
- Structured prompts that request complete, self-contained HTML blocks
- Include "regenerate" instruction in prompt to vary output on retry

**Expected outcome:** End-to-end block generation in 1-3s (Cerebras) or 3-8s (Gemini fallback).

---

### 3. Frontend (Vanilla JS + Minimal CSS)

**Why vanilla:** Faster to build, no build step, easier to debug AI-generated content injection.

**Structure:**
```
frontend/
├── index.html           -- Shell with intro section + block container
├── style.css            -- Clean, readable typography
└── app.js               -- Chat logic, block fetching, DOM manipulation
```

**Page layout:**
```
┌────────────────────────────────────────┐
│           Hero / Intro Section         │  ← Static overview
├────────────────────────────────────────┤
│         Chat Window (collapsible)      │  ← "Who are you? What skills?"
├────────────────────────────────────────┤
│           Generated Block 1            │  ← AI-generated HTML
│  [Suggested] [Action] [Buttons]        │
│  [Click highlighted item]              │
├────────────────────────────────────────┤
│           Generated Block 2            │  ← Appended below
│           ...                          │
├────────────────────────────────────────┤
│     [Text input: Ask a question]       │  ← Fixed at bottom
└────────────────────────────────────────┘
```

**Block rendering approach:**
- AI returns complete HTML string
- Inject via `innerHTML` into a new `<section>` element
- Include inline `<style>` and `<script>` within each block for isolation
- "Regenerate" button on each block calls same endpoint with `regenerate: true`

**Implementation requirements:**
- Maintain minimal client state: `visitorContext`, `previousBlockSummary`, `highlightedItems[]`
- Send context with each `/api/generate-block` call
- Loading spinner during generation
- Error state shows static "AI unavailable" message

**Expected outcome:** Smooth scroll experience, blocks render in-place without page refresh.

---

### 4. Prompt Engineering

**Chat phase prompt (gather context):**
```
You are the intro assistant for [Name]'s resume site.
Ask 1-2 brief questions to understand:
- Who the visitor is (recruiter, engineer, founder, etc.)
- What skills or experiences they're interested in

Be conversational and concise. After gathering context, respond with:
{"ready": true, "visitor_summary": "..."}
```

**Block generation prompt:**
```
You are generating an interactive HTML section for a resume website.

VISITOR CONTEXT: {visitor_summary}
RELEVANT EXPERIENCES: {rag_results}
PREVIOUS BLOCK SUMMARY: {previous_block}
USER ACTION: {action_type: "suggested_button" | "item_click" | "question", value: "..."}

Generate a complete, self-contained HTML block that:
1. Highlights the most relevant experiences for this visitor
2. Uses clean, readable styling (inline <style>)
3. Makes key items clickable with data-item-id attributes
4. Includes 3 suggested action buttons at the bottom
5. Is visually consistent with previous blocks

Return ONLY the HTML. No markdown fences, no explanation.
```

**Implementation requirements:**
- Few-shot examples of good blocks in the system prompt
- Explicit formatting instructions to avoid markdown wrappers
- Request varied output when `regenerate: true` is passed

---

### 5. Docker Compose Setup

NOTE: This will be running on a machine that already has a postgres db running on port 5432. Use port 5433 instead.

```yaml
version: '3.8'
services:
  app:
    build: ./backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5433/resume
      - CEREBRAS_API_KEY=${CEREBRAS_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      - db

  db:
    image: pgvector/pgvector:pg16
    restart: unless-stopped
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=resume
    volumes:
      - pgdata:/var/lib/postgresql/data

  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: resume-site-tunnel
    restart: unless-stopped
    command: tunnel --no-autoupdate run --token ${CLOUDFLARE_TUNNEL_TOKEN}

volumes:
  pgdata:
```

**Implementation requirements:**
- Single `docker-compose up` to run entire stack
- Seed script runs on first startup (or manually via `docker exec`)
- Environment variables for API keys (use `.env` file)

---

## Implementation Sequence

| Phase | Tasks |
|-------|-------|
| **1. Data** | Parse markdown → JSON, write seed script, test pgvector queries |
| **2. Backend** | FastAPI skeleton, LLM clients with fallback, RAG retrieval |
| **3. Prompts** | Iterate on chat + block generation prompts, test outputs |
| **4. Frontend** | Static shell, chat UI, block injection logic, action handlers |
| **5. Integration** | Wire everything together, test full flow |
| **6. Docker** | Dockerfiles, compose, cloudflared config |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| AI generates broken HTML | Regenerate button; prompt engineering to request valid HTML; basic try/catch on render |
| Cerebras rate limits | Gemini fallback; low traffic assumption makes this unlikely |
| Slow generation feels broken | Loading skeleton/spinner |

---

## Out of Scope (Future Enhancements)

- Persistent sessions / conversation history
- Analytics on which blocks users engage with
- A/B testing different prompt strategies
- Mobile-optimized layout
- PDF resume generation from highlighted items

---

## Files to Create

```
project/
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── llm.py
│   ├── rag.py
│   ├── prompts.py
│   ├── models.py
│   ├── db.py
│   └── seed.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
└── data/
    └── resume-item.md          -- Dedicated items for each project/job experience.
```
