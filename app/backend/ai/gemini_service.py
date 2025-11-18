"""Gemini AI service for intelligent mapping and validation."""
import json
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Make Vertex AI imports optional
try:
    from google.cloud import aiplatform
    from vertexai.generative_models import GenerativeModel, Part
    VERTEXAI_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Vertex AI not available: {e}. AI features will run in mock mode.")
    VERTEXAI_AVAILABLE = False
    GenerativeModel = None
    Part = None

from config import settings

class GeminiService:
    """Service for interacting with Vertex AI Gemini models."""
    
    def __init__(self):
        """Initialize Gemini service."""
        if not VERTEXAI_AVAILABLE:
            logger.warning("Vertex AI not available. Service will run in mock mode.")
            self.model = None
            return
            
        try:
            aiplatform.init(
                project=settings.project_id,
                location=settings.vertex_ai_location
            )
            self.model = GenerativeModel(settings.vertex_ai_model)
        except Exception as e:
            logger.warning(f"Could not initialize Gemini service: {e}. Service will run in mock mode.")
            self.model = None
    
    async def map_to_coa(
        self,
        source_items: List[Dict],
        coa_items: List[Dict],
        context: Optional[str] = None
    ) -> List[Dict]:
        """Map source line items to chart of accounts using AI."""
        if self.model is None:
            logger.warning("Gemini model not available, returning empty mappings")
            return []
        
        # Build prompt with source and COA data
        prompt = f"""You are a financial mapping assistant. Map the following source line items to the most appropriate chart of accounts items.

Source Items:
{json.dumps(source_items, indent=2)}

Chart of Accounts:
{json.dumps(coa_items, indent=2)}

{f"Additional Context: {context}" if context else ""}

Return ONLY a JSON array of mappings in this format:
[
  {{
    "source_item_id": "id from source",
    "coa_item_id": "id from COA",
    "confidence": 0.95,
    "reasoning": "brief explanation"
  }}
]
"""
        
        try:
            response = self.model.generate_content(prompt)
            mappings = json.loads(response.text)
            return mappings
        except Exception as e:
            logger.error(f"Error generating mappings: {e}")
            return []
    
    async def chat_response(
        self,
        message: str,
        context: Optional[str] = None,
        history: Optional[List[Dict]] = None
    ) -> str:
        """Generate a chat response using Gemini."""
        if self.model is None:
            return "AI chat is currently unavailable. Please contact support."
        
        full_prompt = message
        if context:
            full_prompt = f"Context: {context}\n\n{message}"
        
        try:
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            return "I encountered an error processing your request. Please try again."

gemini_service = GeminiService()
