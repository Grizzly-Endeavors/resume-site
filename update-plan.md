# Implementation Plan: Dynamic Content Generation with Diversity Scoring

## Overview

This plan implements enhanced content generation with diversity scoring and multi-model support to prevent repetitive content and enable context-aware responses.

## Goals

1. **Diversity Scoring**: Prevent showing the same projects/experiences repeatedly using MMR-Lite algorithm
2. **Context Tracking**: Track recent block + compressed context of what's been covered
3. **Multi-Model Integration**:
   - Cerebras Llama 3.3-70B for button generation (fast, simple JSON)
   - Cerebras Qwen 3-32B for query expansion (better RAG recall)
   - Cerebras Qwen 3-235B for main block generation (current model, high quality)
4. **Prompt Updates**: Integrate diversity and context awareness

## Architecture Changes

### 1. Diversity Scoring (MMR-Lite Algorithm)

**Implementation**: Penalize previously shown experiences without hard filtering

```python
# In rag.py
def apply_diversity_scoring(results: List[Dict], shown_ids: set, penalty: float = 0.3):
    """Apply diversity penalty to already-shown experiences"""
    for result in results:
        if result['id'] in shown_ids:
            result['similarity'] *= (1 - penalty)  # Reduce score by 30%

    # Re-sort by adjusted similarity
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results
```

**Why this approach?**
- Simple and interpretable
- Doesn't exclude relevant content, just de-prioritizes it
- Tuneable via penalty parameter
- Handles edge case: user asks "tell me more about X" → still shows it, just ranked lower

### 2. Context Tracking System

**Two-tier context structure**:

```python
# In models.py
class CompressedContext(BaseModel):
    recent_block_summary: Optional[str] = None  # Detailed summary of last block
    shown_experience_ids: List[str] = []        # All shown experience UUIDs
    topics_covered: List[str] = []              # High-level topics covered
```

**Storage**: Frontend state (no backend session needed)

**Context generation**: Backend generates summary during block creation using structured response format:

```
<block>
[HTML content]
</block>
<summary>
[One sentence describing what was covered]
</summary>
```

### 3. Multi-Model Integration

| Task | Model | Rationale | Fallback |
|------|-------|-----------|----------|
| Button generation | Llama 3.3-70B | Fast, good at JSON, smaller than 235B | Gemini 2.5 Flash |
| Query expansion | Qwen 3-32B | Fast, semantic understanding, improves RAG | Skip expansion (use original) |
| Block generation | Qwen 3-235B | Current model, high quality | Gemini 2.5 Flash |

**Note**: Using Llama 70B instead of 1B because 1B models are too small for reliable JSON generation. Cerebras 70B is still very fast.

**Query expansion flow**:
1. User query → Qwen 32B expands to related terms/synonyms
2. Expanded query → RAG search (better recall)
3. RAG results → Qwen 235B generates block

Example: "leadership" → "leadership team management mentoring coaching project management stakeholder communication"

## Implementation Steps

### Phase 1: Backend Multi-Model Support

**File**: [backend/llm.py](backend/llm.py)

**Changes**:

```python
# Add model constants
CEREBRAS_MODEL_BUTTON = "llama-3.3-70b-instruct"
CEREBRAS_MODEL_QUERY = "qwen-3-32b-instruct"
CEREBRAS_MODEL_BLOCK = "qwen-3-235b-a22b-instruct-2507"

# Add task-specific functions
async def cerebras_call(prompt: str, system_prompt: str, model: str, timeout: int = 10) -> str:
    """Generic Cerebras call with configurable model"""
    # Modify existing function to accept model parameter

async def generate_button_suggestions(system_prompt: str, timeout: int = 10) -> str:
    """Fast button generation using Llama 70B"""
    return await cerebras_call("", system_prompt, CEREBRAS_MODEL_BUTTON, timeout)

async def expand_query(query: str, visitor_summary: str) -> str:
    """Expand search query using Qwen 32B"""
    prompt = f"Visitor: {visitor_summary}\nQuery: {query}"
    try:
        expanded = await cerebras_call(prompt, QUERY_EXPANSION_PROMPT, CEREBRAS_MODEL_QUERY, timeout=5)
        return f"{query} {expanded}"  # Combine original + expanded
    except:
        logger.warning("Query expansion failed, using original query")
        return query  # Fallback to original

async def generate_block_content(prompt: str, system_prompt: str) -> str:
    """High-quality block generation using Qwen 235B"""
    # Existing generate_text() logic, but renamed for clarity
    try:
        return await cerebras_call(prompt, system_prompt, CEREBRAS_MODEL_BLOCK)
    except Exception as e:
        logger.warning(f"Cerebras call failed: {e}. Falling back to Gemini.")
        return await gemini_call(prompt, system_prompt)
```

**New prompt** (add to prompts.py):

```python
QUERY_EXPANSION_PROMPT = """Given a visitor's query about a candidate's resume, expand it with 5-10 related terms, synonyms, and semantic variations for better vector search.

Visitor Context: {visitor_summary}
Original Query: {query}

Return comma-separated terms only. No explanations.

Example:
Input: "leadership experience"
Output: team management, mentoring, coaching, project management, stakeholder communication, organizational skills, agile"""
```

### Phase 2: Data Model Updates

**File**: [backend/models.py](backend/models.py)

**Add new context model**:

```python
class CompressedContext(BaseModel):
    recent_block_summary: Optional[str] = None
    shown_experience_ids: List[str] = []
    topics_covered: List[str] = []
```

**Update request/response models**:

```python
class GenerateBlockRequest(BaseModel):
    visitor_summary: str
    context: Optional[CompressedContext] = None  # NEW: replaces previous_block_summary
    action_type: Optional[str] = None
    action_value: Optional[str] = None
    regenerate: bool = False

    # Keep for backward compatibility during transition
    previous_block_summary: Optional[str] = None

class GenerateBlockResponse(BaseModel):
    html: str
    block_summary: str
    experience_ids: List[str] = []  # NEW: UUIDs of shown experiences

class GenerateButtonsRequest(BaseModel):
    visitor_summary: Optional[str] = None
    chat_history: List[Dict[str, str]] = []
    topics_covered: List[str] = []  # NEW
```

### Phase 3: RAG Diversity Scoring

**File**: [backend/rag.py](backend/rag.py)

**Add diversity scoring function**:

```python
def apply_diversity_scoring(
    results: List[Dict[str, Any]],
    shown_ids: List[str],
    penalty: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Apply diversity penalty to previously shown experiences.

    Args:
        results: RAG search results with 'similarity' scores
        shown_ids: List of experience IDs already shown
        penalty: Reduction factor (0.3 = 30% penalty)

    Returns:
        Re-ranked results
    """
    shown_set = set(shown_ids)

    for result in results:
        if result['id'] in shown_set:
            original_score = result['similarity']
            result['similarity'] *= (1 - penalty)
            logger.info(f"[DIVERSITY] Penalized '{result['title']}': {original_score:.3f} → {result['similarity']:.3f}")

    # Re-sort by adjusted similarity
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results
```

**Update search function**:

```python
async def search_similar_experiences(
    query: str,
    limit: int = 5,
    shown_ids: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """Search with optional diversity scoring"""
    pool = await get_db_pool()

    logger.info(f"[RAG Search] Query: '{query}', Shown IDs: {len(shown_ids) if shown_ids else 0}")
    query_embedding = await generate_embedding(query, task_type="retrieval_query")
    embedding_str = f"[{','.join(map(str, query_embedding))}]"

    async with pool.acquire() as conn:
        # Fetch more results than needed for better diversity (fetch 2x limit)
        fetch_limit = limit * 2 if shown_ids else limit

        rows = await conn.fetch("""
            SELECT id, title, content, skills, metadata,
                   1 - (embedding <=> $1) as similarity
            FROM experiences
            ORDER BY embedding <=> $1
            LIMIT $2
        """, embedding_str, fetch_limit)

        results = []
        for row in rows:
            results.append({
                "id": str(row["id"]),
                "title": row["title"],
                "content": row["content"],
                "skills": row["skills"],
                "metadata": json.loads(row["metadata"]) if isinstance(row["metadata"], str) else row["metadata"],
                "similarity": row["similarity"]
            })

        # Apply diversity scoring if shown_ids provided
        if shown_ids:
            results = apply_diversity_scoring(results, shown_ids)

        # Return requested limit after re-ranking
        return results[:limit]
```

### Phase 4: Prompt Updates

**File**: [backend/prompts.py](backend/prompts.py)

**Update block generation prompt**:

```python
BLOCK_GENERATION_SYSTEM_PROMPT = """
You are generating an interactive HTML section for a resume website.

VISITOR CONTEXT: {visitor_summary}

CONVERSATION CONTEXT:
{context_summary}

RELEVANT EXPERIENCES: {rag_results}

USER ACTION: {action_type} - {action_value}

Generate a complete HTML block that:
1. Highlights the most relevant experiences for this visitor
2. AVOIDS repeating detailed information from the conversation context above
3. If certain topics have been covered, explore new angles or different projects
4. Uses clean, readable styling (inline <style> allowed, prefer dark mode)
5. Be creative and dynamic with layouts, typography, and visual hierarchy
6. Ensure accessibility (semantic HTML, color contrast, readable fonts)
7. Be detailed and specific with concrete examples and data points
8. Long blocks are allowed when they add value
9. Summarize multiple experiences into cohesive narratives when appropriate
10. Be factual and avoid speculation

Format your response as:
<block>
[Your complete HTML content here - this will be inserted directly into the page]
</block>
<summary>
[One concise sentence describing what this block covered - used for context tracking]
</summary>

IMPORTANT:
- Do NOT use markdown code fences (```html)
- The <block> tags are for parsing only, not part of the HTML
- The summary should be semantic (e.g., "Explored AI/ML projects and technical leadership at Company X")
"""

BUTTON_GENERATION_PROMPT = """
You are generating suggested prompt buttons for an AI-powered interactive resume chatbot.

CONTEXT:
- Visitor Summary: {visitor_summary}
- Recent Chat History: {chat_history}
- Topics Already Covered: {topics_covered}

Generate 3 diverse, interesting prompts that:
1. Are specific and actionable
2. Explore DIFFERENT aspects than those already covered
3. Are relevant to the visitor's interests
4. Are phrased as natural questions (e.g., "Tell me about your AI projects")

AVOID suggesting topics that overlap with: {topics_covered}

Return ONLY a JSON array:
[
  {{"label": "Short label (2-4 words)", "prompt": "Full question text"}},
  {{"label": "Short label", "prompt": "Full question text"}},
  {{"label": "Short label", "prompt": "Full question text"}}
]

Return ONLY the JSON array. No markdown, no explanation.
"""
```

### Phase 5: API Integration

**File**: [backend/main.py](backend/main.py)

**Add response parsing helper**:

```python
def parse_block_response(response: str) -> tuple[str, str]:
    """Extract HTML and summary from structured response"""
    block_match = re.search(r'<block>(.*?)</block>', response, re.DOTALL)
    summary_match = re.search(r'<summary>(.*?)</summary>', response, re.DOTALL)

    if block_match and summary_match:
        html = block_match.group(1).strip()
        summary = summary_match.group(1).strip()
    else:
        # Fallback: treat entire response as HTML
        html = response.strip()
        summary = "Displayed relevant experience block"
        logger.warning("Failed to parse structured response, using fallback")

    return html, summary
```

**Update `/api/generate-block` endpoint**:

```python
@app.post("/api/generate-block", response_model=GenerateBlockResponse)
async def generate_block(request: GenerateBlockRequest):
    try:
        # 1. Query Expansion
        query = request.action_value or request.visitor_summary
        expanded_query = await expand_query(query, request.visitor_summary)
        logger.info(f"[QUERY] Original: '{query}' → Expanded: '{expanded_query}'")

        # 2. RAG with Diversity Scoring
        shown_ids = request.context.shown_experience_ids if request.context else []
        experiences = await search_similar_experiences(
            query=expanded_query,
            limit=10,
            shown_ids=shown_ids
        )

        experience_ids = [exp['id'] for exp in experiences]
        rag_results = await format_rag_results(experiences)

        # 3. Build Context Summary
        context_summary = ""
        if request.context:
            if request.context.recent_block_summary:
                context_summary += f"Most Recent Block: {request.context.recent_block_summary}\n"
            if request.context.topics_covered:
                context_summary += f"Topics Already Covered: {', '.join(request.context.topics_covered)}\n"

        # 4. Format Prompt
        formatted_prompt = BLOCK_GENERATION_SYSTEM_PROMPT.format(
            visitor_summary=request.visitor_summary,
            context_summary=context_summary,
            rag_results=rag_results,
            action_type=request.action_type or "initial_load",
            action_value=request.action_value or "None"
        )

        # 5. Generate Block
        response = await generate_block_content("Generate the next block with summary.", formatted_prompt)

        # 6. Parse Response
        html, summary = parse_block_response(response)

        return GenerateBlockResponse(
            html=html,
            block_summary=summary,
            experience_ids=experience_ids
        )

    except Exception as e:
        logger.error(f"Block generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

**Update `/api/generate-buttons` endpoint**:

```python
@app.post("/api/generate-buttons", response_model=GenerateButtonsResponse)
async def generate_buttons(request: GenerateButtonsRequest):
    try:
        # Format chat history
        history_text = ""
        for msg in request.chat_history[-6:]:
            role = "Visitor" if msg.get("role") == "user" else "Assistant"
            history_text += f"{role}: {msg.get('content', '')}\n"

        topics_covered = ", ".join(request.topics_covered) if request.topics_covered else "None"

        # Construct prompt
        formatted_prompt = BUTTON_GENERATION_PROMPT.format(
            visitor_summary=request.visitor_summary or "Unknown visitor",
            chat_history=history_text if history_text else "No prior conversation",
            topics_covered=topics_covered
        )

        # Generate using Llama 70B (fast JSON generation)
        response_text = await generate_button_suggestions(formatted_prompt)

        # Parse JSON (existing logic)
        # ... existing code ...
```

### Phase 6: Frontend Context Tracking

**File**: [frontend/app.js](frontend/app.js)

**Add context tracker**:

```javascript
// Replace single previousBlockSummary with comprehensive tracker
let contextTracker = {
    recentBlockSummary: null,
    shownExperienceIds: new Set(),
    topicsCovered: new Set()
};
```

**Update `generateBlock` function**:

```javascript
async function generateBlock(actionType, actionValue, blockId = null) {
    try {
        // Build context object from tracker
        const context = {
            recent_block_summary: contextTracker.recentBlockSummary,
            shown_experience_ids: Array.from(contextTracker.shownExperienceIds),
            topics_covered: Array.from(contextTracker.topicsCovered)
        };

        const res = await fetch('/api/generate-block', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                visitor_summary: visitorSummary,
                context: context,  // NEW: send full context
                action_type: actionType,
                action_value: actionValue
            })
        });

        const data = await res.json();

        // Update context tracker
        contextTracker.recentBlockSummary = data.block_summary;

        // Track shown experience IDs
        if (data.experience_ids) {
            data.experience_ids.forEach(id => {
                contextTracker.shownExperienceIds.add(id);
            });
        }

        // Extract and track topic from summary
        const topic = extractTopicFromSummary(data.block_summary);
        if (topic) {
            contextTracker.topicsCovered.add(topic);
        }

        // Existing rendering logic...
        // ...

    } catch (error) {
        console.error('[generateBlock] Error:', error);
    }
}

function extractTopicFromSummary(summary) {
    /**
     * Simple heuristic: extract key topic from summary
     * Example: "Explored AI/ML projects at Company X" → "AI/ML projects"
     */
    if (!summary) return null;

    // Try to extract content between common verbs and prepositions
    const match = summary.match(/(?:Explored|Displayed|Showed|Highlighted)\s+(.+?)(?:\s+at|\s+from|\s+in|$)/i);
    if (match && match[1]) {
        return match[1].trim();
    }

    // Fallback: use first half of summary (up to 50 chars)
    return summary.substring(0, 50).trim();
}
```

**Update `loadSuggestedButtons` function**:

```javascript
async function loadSuggestedButtons() {
    try {
        const res = await fetch('/api/generate-buttons', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                visitor_summary: visitorSummary,
                chat_history: chatHistoryData,
                topics_covered: Array.from(contextTracker.topicsCovered)  // NEW
            })
        });

        // ... existing code ...
    } catch (error) {
        console.error('[loadSuggestedButtons] Error:', error);
    }
}
```

## Testing Strategy

### Unit Tests

1. **RAG Diversity Scoring** (`backend/tests/test_rag.py`):
   - Test with empty shown_ids (should match current behavior)
   - Test with shown_ids (should re-rank results)
   - Test edge case: all top results already shown

2. **LLM Functions** (`backend/tests/test_llm.py`):
   - Mock Cerebras responses for each model
   - Test fallback logic (Cerebras failure → Gemini)
   - Test query expansion (original + expanded)

3. **Response Parsing** (`backend/tests/test_main.py`):
   - Test `parse_block_response` with valid structured response
   - Test fallback when tags missing

### Integration Tests

1. **Full Flow**:
   - Generate 5 blocks in sequence
   - Verify no duplicate experiences in top 3 results
   - Verify context accumulates properly

2. **Button Generation**:
   - Generate buttons after covering "AI projects"
   - Verify suggested topics are different (e.g., leadership, not more AI)

3. **Regeneration**:
   - Regenerate same block
   - Verify context persists

### Manual Testing Checklist

- [ ] Generate block about "AI projects" → verify relevant experiences shown
- [ ] Generate block about "leadership" → verify different experiences (e.g., esports management)
- [ ] Check browser console: verify `contextTracker` updates after each block
- [ ] Check backend logs: verify diversity penalties applied
- [ ] Test regenerate button: verify context maintained
- [ ] Test suggested buttons: verify topics don't repeat

## Rollout & Monitoring

### Environment Variables

No new environment variables needed (all models use existing `CEREBRAS_API_KEY`).

### Deployment Steps

1. Deploy backend changes
2. Deploy frontend changes
3. Monitor logs for:
   - Diversity scoring activity: `[DIVERSITY]` logs
   - Query expansion: `[QUERY]` logs
   - Context tracking: `[CONTEXT]` logs
   - Model usage: `[MODEL]` logs

### Success Metrics

- **Diversity**: Average blocks before first repeat > 3
- **Performance**: Block generation latency < 5s (including query expansion)
- **Quality**: User regeneration rate < 20%

## Key Files Modified

1. [backend/llm.py](backend/llm.py) - Multi-model support, query expansion
2. [backend/rag.py](backend/rag.py) - Diversity scoring algorithm
3. [backend/models.py](backend/models.py) - CompressedContext data structure
4. [backend/prompts.py](backend/prompts.py) - Context-aware prompts
5. [backend/main.py](backend/main.py) - API integration, response parsing
6. [frontend/app.js](frontend/app.js) - Context tracker, updated API calls

## Trade-offs & Considerations

### Query Expansion
- **Benefit**: Better RAG recall (find more relevant experiences)
- **Cost**: +200-500ms latency per block
- **Mitigation**: Use fast 32B model, 5s timeout, fallback to original query

### Frontend Context Storage
- **Benefit**: Simple, no backend state needed
- **Cost**: Lost on page refresh
- **Future**: Can migrate to backend sessions if needed

### Diversity Penalty (30%)
- **Benefit**: Balances relevance vs novelty
- **Tuneable**: Can adjust penalty parameter based on results
- **Edge case**: User asks "tell me more about X" → still shows it (just lower ranked)

## Future Enhancements

1. **Semantic Deduplication**: Track content similarity, not just IDs
2. **Time Decay**: Old shown experiences get lower penalties
3. **User Preference Learning**: Boost content similar to engaged blocks
4. **Advanced Context**: Multi-turn conversation support ("tell me more about that")
