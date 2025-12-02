import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import json
from rag import search_similar_experiences, format_rag_results, apply_diversity_scoring

@pytest.mark.asyncio
async def test_apply_diversity_scoring():
    results = [
        {"id": "A", "title": "A", "similarity": 0.9},
        {"id": "B", "title": "B", "similarity": 0.8},
        {"id": "C", "title": "C", "similarity": 0.7}
    ]
    shown_ids = ["A"]
    
    # Apply penalty
    new_results = apply_diversity_scoring(results, shown_ids, penalty=0.5)
    
    # A should be penalized: 0.9 * (1 - 0.5) = 0.45
    # B should be unchanged: 0.8
    # C should be unchanged: 0.7
    # Sorted order should be B, C, A
    
    assert new_results[0]["id"] == "B"
    assert new_results[1]["id"] == "C"
    assert new_results[2]["id"] == "A"
    assert new_results[2]["similarity"] == 0.45

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
        
        # Check results
        assert len(results) == 1
        assert results[0]["title"] == "Test Experience"

@pytest.mark.asyncio
async def test_search_similar_experiences_with_diversity():
    # Mock data
    query = "test query"
    mock_embedding = [0.1] * 768
    mock_rows = [
        {"id": "1", "title": "1", "content": "c", "skills": [], "metadata": "{}", "similarity": 0.95},
        {"id": "2", "title": "2", "content": "c", "skills": [], "metadata": "{}", "similarity": 0.90}
    ]

    with patch("rag.get_db_pool", new_callable=AsyncMock) as mock_get_pool, \
         patch("rag.generate_embedding", new_callable=AsyncMock) as mock_gen_embedding:
        
        mock_gen_embedding.return_value = mock_embedding
        mock_pool = MagicMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_get_pool.return_value = mock_pool
        mock_conn.fetch.return_value = mock_rows

        # 1. Test without shown_ids (default)
        results = await search_similar_experiences(query, limit=2)
        assert len(results) == 2
        assert results[0]["id"] == "1"
        assert results[0]["similarity"] == 0.95

        # 2. Test with shown_ids
        # If "1" is shown, it should be penalized.
        # "1" similarity becomes 0.95 * 0.7 = 0.665
        # "2" similarity stays 0.90
        # So "2" should be first now.
        
        results_div = await search_similar_experiences(query, limit=2, shown_ids=["1"])
        
        assert results_div[0]["id"] == "2"
        assert results_div[1]["id"] == "1"
        assert results_div[1]["similarity"] < 0.90

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