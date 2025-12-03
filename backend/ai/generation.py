import logging
import json
import re
from typing import List, Optional, Dict, Any

from ai.llm import llm_handler, ModelSize, StructuredOutputError
from rag import search_similar_experiences, format_rag_results
from ai.prompts import (
    CHAT_SYSTEM_PROMPT,
    BLOCK_GENERATION_SYSTEM_PROMPT,
    BUTTON_GENERATION_PROMPT,
    PROMPT_GENERATION_PROMPT,
    SUMMARY_GENERATION_PROMPT
)
from models import CompressedContext, SuggestedButton, ButtonList, GeneratedPrompt

logger = logging.getLogger(__name__)


class GenerationHandler:
    """Consolidates prompt handling and generation logic for different request types."""

    def __init__(self):
        self.llm = llm_handler

    async def generate_chat_response(
        self,
        message: str,
        history: List[Dict[str, str]],
        user_turns: int
    ) -> Dict[str, Any]:
        """
        Generate chat response for onboarding conversation.

        Returns:
            Dict with 'ready', 'message', and optionally 'visitor_summary'
        """
        # Build history text
        history_text = ""
        for msg in history:
            role = "Visitor" if msg.get("role") == "user" else "Assistant"
            history_text += f"{role}: {msg.get('content')}\n"

        if message:
            history_text += f"Visitor: {message}\n"

        # Build system prompt with turn-based hints
        system_instruction = CHAT_SYSTEM_PROMPT
        if user_turns >= 5:
            system_instruction += "\n\nCRITICAL: You have reached the maximum conversation turns. You MUST now respond with the visitor summary in XML tags. Summarize what you know so far."
        elif user_turns >= 2:
            system_instruction += "\n\nNote: You have gathered enough information. Please wrap up the conversation and provide the visitor summary in XML tags."

        full_prompt = f"{history_text}\nAssistant:"

        # Generate response using large model for quality
        response_text = await self.llm.llm_call(
            prompt=full_prompt,
            system_prompt=system_instruction,
            size=ModelSize.LARGE,
            timeout=30
        )

        # Parse response for XML tags
        import re
        match = re.search(r'<visitor_summary>(.*?)</visitor_summary>', response_text, re.DOTALL)
        if match:
            visitor_summary = match.group(1).strip()
            return {
                "ready": True,
                "visitor_summary": visitor_summary,
                "message": None
            }
        else:
            return {"ready": False, "message": response_text}

    async def generate_prompt(
        self,
        visitor_summary: str,
        block_summaries: List[str],
        user_input: str,
        rag_results: str,
        rag_experiences: List[Dict[str, Any]]
    ) -> GeneratedPrompt:
        """
        Filter RAG results and generate block focus/structure guidance.

        Args:
            visitor_summary: Who the visitor is and what they're looking for
            block_summaries: List of previous block summaries
            user_input: Current user action (button or chat input)
            rag_results: Formatted RAG results text
            rag_experiences: List of experience dicts with 'title' field

        Returns:
            GeneratedPrompt with block_focus, suggested_html_structure, and selected_experience_titles
        """
        block_summaries_text = "\n".join(f"- {summary}" for summary in block_summaries) if block_summaries else "No prior blocks"
        formatted_prompt = PROMPT_GENERATION_PROMPT.format(
            visitor_summary=visitor_summary,
            block_summaries=block_summaries_text,
            user_input=user_input,
            rag_results=rag_results
        )

        try:
            result = await self.llm.output_structure(
                prompt="Generate the prompt.",
                system_prompt=formatted_prompt,
                size=ModelSize.MEDIUM,
                response_model=GeneratedPrompt,
                timeout=10
            )
            logger.info(f"[PROMPT] Block focus: '{result.block_focus}'")
            logger.info(f"[PROMPT] Suggested structure: '{result.suggested_html_structure}'")
            logger.info(f"[PROMPT] Selected experiences: {result.selected_experience_titles}")
            return result
        except StructuredOutputError as e:
            logger.warning(f"Structured prompt generation failed: {e}, using fallback")
            # Fallback: select first 3 experience titles
            fallback_titles = [exp['title'] for exp in rag_experiences[:3]]
            return GeneratedPrompt(
                block_focus="Relevant content based on visitor interests",
                suggested_html_structure="Clean, readable layout with semantic HTML",
                selected_experience_titles=fallback_titles
            )

    async def generate_block(
        self,
        visitor_summary: str,
        action_type: str,
        action_value: str,
        context: Optional[CompressedContext]
    ) -> Dict[str, Any]:
        """
        Generate HTML block content with RAG.

        Returns:
            Dict with 'html', 'block_summary', and 'experience_ids'
        """
        # 1. Perform RAG search with user input query
        user_input = action_value or visitor_summary
        shown_counts = context.shown_experience_counts if context else {}
        experiences = await search_similar_experiences(
            query=user_input,
            limit=5,
            shown_counts=shown_counts
        )

        rag_results = await format_rag_results(experiences)

        # 2. Generate Prompt (filters RAG results and provides focus/structure)
        block_summaries = context.block_summaries if context else []
        generated_prompt = await self.generate_prompt(
            visitor_summary=visitor_summary,
            block_summaries=block_summaries,
            user_input=user_input,
            rag_results=rag_results,
            rag_experiences=experiences
        )

        # 3. Filter experiences based on selected titles and format for block generation
        selected_experiences = [exp for exp in experiences if exp['title'] in generated_prompt.selected_experience_titles]
        selected_rag_results = await format_rag_results(selected_experiences)
        experience_ids = [exp['id'] for exp in selected_experiences]

        logger.info(f"[BLOCK] Selected {len(experience_ids)} experiences for block generation")

        # 4. Format System Prompt with focus and structure guidance
        formatted_prompt = BLOCK_GENERATION_SYSTEM_PROMPT.format(
            block_focus=generated_prompt.block_focus,
            suggested_html_structure=generated_prompt.suggested_html_structure,
            rag_results=selected_rag_results
        )

        # 5. Generate Block (Large model for quality)
        response = await self.llm.llm_call(
            prompt="Generate the next block.",
            system_prompt=formatted_prompt,
            size=ModelSize.LARGE,
            timeout=30
        )

        # 6. Parse HTML from response
        html = self._extract_block_html(response)

        # 7. Generate summary separately with small model
        summary = await self._generate_block_summary(html, visitor_summary)

        return {
            "html": html,
            "block_summary": summary,
            "experience_ids": experience_ids
        }

    def _extract_block_html(self, response: str) -> str:
        """Extract HTML content from block generation response."""
        # The response should be pure HTML now (no XML tags)
        # Clean up any potential markdown artifacts
        html = response.strip()
        html = html.replace("```html", "").replace("```", "").strip()
        return html

    async def _generate_block_summary(self, html: str, visitor_summary: str) -> str:
        """
        Generate a concise summary of what the block covered using small model.

        Args:
            html: The generated HTML content
            visitor_summary: Context about the visitor

        Returns:
            One-sentence summary
        """
        formatted_prompt = SUMMARY_GENERATION_PROMPT.format(
            html=html,
            visitor_summary=visitor_summary
        )

        try:
            summary = await self.llm.llm_call(
                prompt="Generate the summary.",
                system_prompt=formatted_prompt,
                size=ModelSize.SMALL,
                timeout=5
            )
            return summary.strip()
        except Exception as e:
            logger.warning(f"Summary generation failed: {e}, using fallback")
            return "Displayed relevant experience block"

    async def generate_buttons(
        self,
        visitor_summary: str,
        chat_history: List[Dict[str, str]],
        context: Optional[CompressedContext]
    ) -> List[SuggestedButton]:
        """
        Generate suggested prompt buttons based on RAG items and visitor summary.

        Returns:
            List of SuggestedButton objects
        """
        # Find the most recent user message for RAG search
        search_query = visitor_summary  # fallback
        for msg in reversed(chat_history):
            if msg.get("role") == "user":
                search_query = msg.get("content", "")
                break

        # RAG Search - get relevant experiences
        shown_counts = context.shown_experience_counts if context else {}
        experiences = await search_similar_experiences(
            query=search_query,
            limit=5,
            shown_counts=shown_counts
        )
        rag_results = await format_rag_results(experiences)

        # Construct prompt with visitor summary
        formatted_prompt = BUTTON_GENERATION_PROMPT.format(
            visitor_summary=visitor_summary,
            rag_results=rag_results
        )

        # Generate using structured output method
        try:
            button_list = await self.llm.output_structure(
                prompt="Generate suggested buttons.",
                system_prompt=formatted_prompt,
                size=ModelSize.SMALL,
                response_model=ButtonList,
                timeout=10
            )
            logger.info(f"Successfully generated {len(button_list.buttons)} buttons via structured output")
            return button_list.buttons

        except StructuredOutputError as e:
            # All retries and fallback failed - return static buttons
            logger.warning(f"Button generation failed after all attempts: {e}. Using fallback.")
            return [
                SuggestedButton(label="Experience", prompt="Tell me about your professional experience"),
                SuggestedButton(label="Skills", prompt="What are your key technical skills?"),
                SuggestedButton(label="Projects", prompt="Show me some of your notable projects")
            ]


# Global generation handler instance
generation_handler = GenerationHandler()
