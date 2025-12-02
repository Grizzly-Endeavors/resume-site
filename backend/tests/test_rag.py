import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import json
from rag import search_similar_experiences, format_rag_results

@pytest.mark.asyncio
async def test_search_similar_experiences():
    # Mock data
    query = "test query"
    mock_embedding = [0.1, 0.2, 0.3]
    mock_rows = [
        {
            "id": "123",
            "title": "Test Experience",
            "content": "This is a test content.",
            "skills": ["Python", "Testing"],
            "metadata": '{"key": "value"}',
            "similarity": 0.95
        }
    ]

    # Mock dependencies
    with patch("rag.get_db_pool", new_callable=AsyncMock) as mock_get_pool, \
         patch("rag.generate_embedding", new_callable=AsyncMock) as mock_gen_embedding:
        
        mock_gen_embedding.return_value = mock_embedding
        
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_get_pool.return_value = mock_pool
        
        mock_conn.fetch.return_value = mock_rows

        # Run function
        results = await search_similar_experiences(query)

        # Assertions
        mock_gen_embedding.assert_awaited_once_with(query, task_type="retrieval_query")
        mock_get_pool.assert_awaited_once()
        mock_conn.fetch.assert_awaited_once()
        
        # Check SQL arguments
        args = mock_conn.fetch.call_args[0]
        assert "SELECT id, title" in args[0]
        assert args[1] == f"[{','.join(map(str, mock_embedding))}]"
        assert args[2] == 5 # default limit

        # Check results
        assert len(results) == 1
        assert results[0]["title"] == "Test Experience"
        assert results[0]["skills"] == ["Python", "Testing"]
        assert results[0]["metadata"] == {"key": "value"}
        assert results[0]["similarity"] == 0.95

@pytest.mark.asyncio
async def test_format_rag_results():
    results = [
        {
            "title": "Job A",
            "skills": ["Skill 1", "Skill 2"],
            "content": "Did some work."
        },
        {
            "title": "Job B",
            "skills": [],
            "content": "Did other work."
        }
    ]
    
    formatted = await format_rag_results(results)
    
    assert "Title: Job A" in formatted
    assert "Skills: Skill 1, Skill 2" in formatted
    assert "Content: Did some work."
    assert "Title: Job B" in formatted
    assert "Skills: N/A" in formatted
    assert "Content: Did other work."
    assert "---\n" in formatted
