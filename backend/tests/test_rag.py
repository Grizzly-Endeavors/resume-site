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
    shown_counts = {"A": 1}

    # Apply penalty
    new_results = apply_diversity_scoring(results, shown_counts, penalty_per_showing=0.5)

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

    # Create mock rows that behave like dict
    class MockRow:
        def __init__(self, data):
            self._data = data

        def __getitem__(self, key):
            return self._data[key]

    mock_rows = [
        MockRow({
            "id": "123",
            "title": "Test Experience",
            "content": "This is a test content.",
            "skills": '["Python", "Testing"]',
            "metadata": '{"key": "value"}',
            "distance": 0.05
        })
    ]

    # Mock dependencies
    with patch("rag.get_db", new_callable=AsyncMock) as mock_get_db, \
         patch("ai.llm.llm_handler.generate_embedding", new_callable=AsyncMock) as mock_gen_embedding:

        mock_gen_embedding.return_value = mock_embedding

        mock_db = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = mock_rows
        mock_db.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        # Run function
        results = await search_similar_experiences(query)

        # Assertions
        mock_gen_embedding.assert_awaited_once_with(query, task_type="retrieval_query")
        mock_get_db.assert_awaited_once()

        # Check results
        assert len(results) == 1
        assert results[0]["title"] == "Test Experience"


@pytest.mark.asyncio
async def test_search_similar_experiences_with_diversity():
    # Mock data
    query = "test query"
    mock_embedding = [0.1] * 768

    # Create mock rows that behave like dict
    class MockRow:
        def __init__(self, data):
            self._data = data

        def __getitem__(self, key):
            return self._data[key]

    mock_rows = [
        MockRow({"id": "1", "title": "1", "content": "c", "skills": "[]", "metadata": "{}", "distance": 0.05}),
        MockRow({"id": "2", "title": "2", "content": "c", "skills": "[]", "metadata": "{}", "distance": 0.10})
    ]

    with patch("rag.get_db", new_callable=AsyncMock) as mock_get_db, \
         patch("ai.llm.llm_handler.generate_embedding", new_callable=AsyncMock) as mock_gen_embedding:

        mock_gen_embedding.return_value = mock_embedding
        mock_db = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchall.return_value = mock_rows
        mock_db.execute.return_value = mock_cursor
        mock_get_db.return_value = mock_db

        # 1. Test without shown_ids (default)
        results = await search_similar_experiences(query, limit=2)
        assert len(results) == 2
        assert results[0]["id"] == "1"  # Lower distance = higher similarity

        # 2. Test with shown_counts - need to reset mock
        mock_cursor.fetchall.return_value = mock_rows
        results_div = await search_similar_experiences(query, limit=2, shown_counts={"1": 1})

        # With diversity scoring, "1" should be penalized
        assert results_div[0]["id"] == "2"
        assert results_div[1]["id"] == "1"


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
