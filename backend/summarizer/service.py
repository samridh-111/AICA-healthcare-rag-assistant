import json
import logging
from typing import List, Dict, Any
from backend.groq.provider import get_llm_provider
from backend.prompts.summary_prompt import get_summary_system_prompt, get_summary_user_prompt
from backend.summarizer.schemas import ConversationSummary
from backend.config import SUMMARIZATION_MESSAGE_THRESHOLD

logger = logging.getLogger(__name__)

class SummarizerService:
    def __init__(self):
        self.provider = get_llm_provider()
        
    def should_summarize(self, message_count: int) -> bool:
        """Returns True if message_count is >= the configured threshold."""
        return message_count >= SUMMARIZATION_MESSAGE_THRESHOLD
        
    async def summarize_conversation(self, conversation_history: List[Dict[str, str]]) -> ConversationSummary:
        """
        Takes a list of conversation messages and extracts a structured clinical summary.
        Messages should have 'role' (e.g., 'user', 'assistant') and 'content'.
        """
        # Format the conversation history
        formatted_history = ""
        for msg in conversation_history:
            role = msg.get("role", "unknown").capitalize()
            content = msg.get("content", "")
            formatted_history += f"{role}: {content}\n\n"
            
        system_prompt = get_summary_system_prompt()
        user_prompt = get_summary_user_prompt(formatted_history.strip())
        
        try:
            response_str = await self.provider.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_format={"type": "json_object"}
            )
            
            data = json.loads(response_str)
            return ConversationSummary(**data)
            
        except Exception as e:
            logger.error(f"Failed to summarize conversation: {e}")
            # Return empty summary on failure
            return ConversationSummary()
