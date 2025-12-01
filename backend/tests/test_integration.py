import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app
from models import GenerateBlockRequest

client = TestClient(app)

@pytest.mark.asyncio
async def test_generate_block_integrates_rag_into_prompt():
    # Mock Data
    mock_rag_results = [
        {"title": "Test Job", "content": "Test Content", "skills": ["Skill1"], "metadata": {}, "id": "1", "similarity": 0.9}
    ]
    mock_formatted_rag = "Title: Test Job\nSkills: Skill1\nContent: Test Content\n---\n"
    
    # Mock Dependencies
    with patch("main.search_similar_experiences", new_callable=AsyncMock) as mock_search, \
         patch("main.format_rag_results", new_callable=AsyncMock) as mock_format, \
         patch("main.generate_text", new_callable=AsyncMock) as mock_generate:
        
        mock_search.return_value = mock_rag_results
        mock_format.return_value = mock_formatted_rag
        mock_generate.return_value = "<section>Mock HTML</section>"

        # Make Request
        request_data = {
            "visitor_summary": "Recruiter looking for Python dev",
            "action_type": "initial_load",
            "action_value": None,
            "previous_block_summary": None,
            "regenerate": False
        }
        
        response = client.post("/api/generate-block", json=request_data)

        # Verify Response
        assert response.status_code == 200
        assert response.json()["html"] == "<section>Mock HTML</section>"
        
        # KEY CHECK: Verify RAG results were in the prompt
        # We need to get the arguments passed to generate_text
        mock_generate.assert_awaited_once()
        call_args = mock_generate.call_args
        prompt_arg = call_args[0][1] # system_prompt is the second arg in generate_text(prompt, system_prompt) or first?
        # In main.py: await generate_text("Generate the next block.", formatted_prompt)
        # So formatted_prompt is the second argument (system_prompt).
        
        assert mock_formatted_rag in prompt_arg
        assert "RELEVANT EXPERIENCES:" in prompt_arg
        assert "Recruiter looking for Python dev" in prompt_arg # Visitor context
