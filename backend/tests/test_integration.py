import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from main import app, parse_block_response
from models import GenerateBlockRequest

client = TestClient(app)

def test_parse_block_response():
    response = """
    <block>
    <div>HTML Content</div>
    </block>
    <summary>
    Summary text
    </summary>
    """
    html, summary = parse_block_response(response)
    assert html == "<div>HTML Content</div>"
    assert summary == "Summary text"

def test_parse_block_response_fallback():
    response = "<div>Just HTML</div>"
    html, summary = parse_block_response(response)
    assert html == "<div>Just HTML</div>"
    assert summary == "Displayed relevant experience block"

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
         patch("main.generate_block_content", new_callable=AsyncMock) as mock_generate, \
         patch("main.expand_query", new_callable=AsyncMock) as mock_expand:
        
        mock_expand.return_value = "expanded query"
        mock_search.return_value = mock_rag_results
        mock_format.return_value = mock_formatted_rag
        mock_generate.return_value = "<block><section>Mock HTML</section></block><summary>Summary</summary>"

        # Make Request
        request_data = {
            "visitor_summary": "Recruiter looking for Python dev",
            "action_type": "initial_load",
            "action_value": None,
            "regenerate": False,
            "context": {
                "shown_experience_ids": []
            }
        }
        
        response = client.post("/api/generate-block", json=request_data)

        # Verify Response
        assert response.status_code == 200
        assert response.json()["html"] == "<section>Mock HTML</section>"
        
        # Verify expand called
        mock_expand.assert_awaited_once()

        # KEY CHECK: Verify RAG results were in the prompt
        mock_generate.assert_awaited_once()
        call_args = mock_generate.call_args
        prompt_arg = call_args[0][1] 
        
        assert mock_formatted_rag in prompt_arg
        assert "RELEVANT EXPERIENCES:" in prompt_arg
        assert "Recruiter looking for Python dev" in prompt_arg

@pytest.mark.asyncio
async def test_generate_buttons_integrates_rag():
    # Mock Data
    mock_rag_results = [
        {"title": "Test Job", "content": "Test Content", "skills": ["Skill1"], "metadata": {}, "id": "1", "similarity": 0.9}
    ]
    mock_formatted_rag = "Title: Test Job\nSkills: Skill1\nContent: Test Content\n---\n"
    
    # Mock Dependencies
    with patch("main.search_similar_experiences", new_callable=AsyncMock) as mock_search, \
         patch("main.format_rag_results", new_callable=AsyncMock) as mock_format, \
         patch("main.generate_button_suggestions", new_callable=AsyncMock) as mock_generate_buttons, \
         patch("main.expand_query", new_callable=AsyncMock) as mock_expand:
        
        mock_expand.return_value = "expanded query"
        mock_search.return_value = mock_rag_results
        mock_format.return_value = mock_formatted_rag
        mock_generate_buttons.return_value = '[{"label": "Test Button", "prompt": "Test Prompt"}]'

        # Make Request with new context structure
        request_data = {
            "visitor_summary": "Recruiter",
            "chat_history": [{"role": "user", "content": "Hi"}],
            "context": {
                "shown_experience_ids": ["123"],
                "topics_covered": ["Intro"],
                "recent_block_summary": "Summary"
            }
        }
        
        response = client.post("/api/generate-buttons", json=request_data)

        # Verify Response
        assert response.status_code == 200
        assert len(response.json()["buttons"]) == 1
        
        # Verify RAG search was performed with shown_ids
        mock_search.assert_awaited_once()
        _, kwargs = mock_search.call_args
        assert kwargs["shown_ids"] == ["123"]

        # Verify RAG results were in the prompt
        mock_generate_buttons.assert_awaited_once()
        call_args = mock_generate_buttons.call_args
        prompt_arg = call_args[0][0] # prompt is first arg
        
        assert mock_formatted_rag in prompt_arg
        assert "RELEVANT CONTENT:" in prompt_arg