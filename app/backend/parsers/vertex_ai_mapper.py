"""Vertex AI service for mapping line items to canonical COA."""
import logging
import json
from typing import Dict, Any, List
from config import settings

logger = logging.getLogger(__name__)

# Make Vertex AI imports optional
try:
    from google.cloud import aiplatform
    from vertexai.generative_models import GenerativeModel, Part
    VERTEXAI_AVAILABLE = True
    aiplatform.init(project=settings.project_id, location=settings.vertex_ai_location)
except ImportError as e:
    logger.warning(f"Vertex AI not available: {e}. Mapper will run in mock mode.")
    VERTEXAI_AVAILABLE = False
    GenerativeModel = None


class VertexAIMapper:
    """Use Vertex AI to map financial line items to canonical chart of accounts."""
    
    def __init__(self):
        if VERTEXAI_AVAILABLE:
            self.model = GenerativeModel(settings.vertex_ai_model)
        else:
            self.model = None
    
    def map_line_items(
        self,
        line_items: List[str],
        canonical_coa: List[Dict[str, str]],
        statement_type: str
    ) -> List[Dict[str, Any]]:
        """Map extracted line items to canonical COA using AI."""
        if self.model is None:
            logger.warning("Vertex AI not available, returning unmapped items")
            return self._create_default_mappings(line_items)
        
        logger.info(f"Mapping {len(line_items)} line items using Vertex AI")
        
        try:
            prompt = self._build_mapping_prompt(line_items, canonical_coa, statement_type)
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.1,
                    "top_p": 0.95,
                    "max_output_tokens": 2048,
                }
            )
            
            mappings = self._parse_mapping_response(response.text, line_items)
            return mappings
            
        except Exception as e:
            logger.error(f"Error mapping line items with Vertex AI: {str(e)}")
            return [
                {
                    "source_label": item,
                    "canonical_code": None,
                    "canonical_label": None,
                    "confidence": 0.0,
                    "error": str(e)
                }
                for item in line_items
            ]
    
    def _build_mapping_prompt(
        self,
        line_items: List[str],
        canonical_coa: List[Dict[str, str]],
        statement_type: str
    ) -> str:
        """Build prompt for COA mapping."""
        coa_sample = canonical_coa[:50] if len(canonical_coa) > 50 else canonical_coa
        coa_text = "\n".join([f"- {item['code']}: {item['label']} (aliases: {item.get('aliases', 'N/A')})" for item in coa_sample])
        
        prompt = f"""You are a financial analysis expert. Your task is to map source financial statement line items to a canonical chart of accounts (COA).

Statement Type: {statement_type}

Canonical COA (sample):
{coa_text}

Source Line Items to Map:
{json.dumps(line_items, indent=2)}

Instructions:
1. For each source line item, find the best matching canonical COA code.
2. Consider aliases and common variations.
3. Return a JSON array with this structure:
[
  {{
    "source_label": "Original Label",
    "canonical_code": "COA_CODE",
    "canonical_label": "Canonical Label",
    "confidence": 0.95,
    "reasoning": "Brief explanation"
  }}
]

4. If no good match exists, use confidence < 0.5 and suggest the closest match.
5. Confidence scale: 1.0 = exact match, 0.8-0.99 = strong match, 0.5-0.79 = probable match, <0.5 = uncertain

Return ONLY the JSON array, no additional text."""
        
        return prompt
    
    def _parse_mapping_response(self, response_text: str, line_items: List[str]) -> List[Dict[str, Any]]:
        """Parse AI response into structured mappings."""
        try:
            response_text = response_text.strip()
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_text = response_text[start_idx:end_idx]
                mappings = json.loads(json_text)
                return mappings
            else:
                logger.warning("No JSON array found in AI response")
                return self._create_default_mappings(line_items)
                
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing AI response as JSON: {str(e)}")
            return self._create_default_mappings(line_items)
    
    def _create_default_mappings(self, line_items: List[str]) -> List[Dict[str, Any]]:
        """Create default unmapped entries."""
        return [
            {
                "source_label": item,
                "canonical_code": None,
                "canonical_label": None,
                "confidence": 0.0,
                "reasoning": "Automatic mapping failed"
            }
            for item in line_items
        ]
    
    def detect_missing_fields(self, parsed_data: Dict[str, Any], statement_type: str) -> List[Dict[str, Any]]:
        """Use AI to detect missing or inconsistent fields in financial data."""
        if self.model is None:
            logger.warning("Vertex AI not available, skipping field detection")
            return []
        
        logger.info(f"Detecting missing fields in {statement_type}")
        
        try:
            prompt = f"""You are a financial analysis expert. Review this {statement_type} and identify:
1. Missing critical line items
2. Inconsistencies or anomalies
3. Fields that should exist but don't

Parsed Data:
{json.dumps(parsed_data, indent=2)[:2000]}

Return a JSON array of issues:
[
  {{
    "issue_type": "missing_field" | "inconsistency" | "anomaly",
    "severity": "error" | "warning" | "info",
    "description": "Description of the issue",
    "affected_items": ["list", "of", "items"],
    "suggestion": "How to fix it",
    "confidence": 0.85
  }}
]

Return ONLY the JSON array."""
            
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 1024,
                }
            )
            
            response_text = response.text.strip()
            start_idx = response_text.find('[')
            end_idx = response_text.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_text = response_text[start_idx:end_idx]
                issues = json.loads(json_text)
                return issues
            
            return []
            
        except Exception as e:
            logger.error(f"Error detecting missing fields: {str(e)}")
            return []
