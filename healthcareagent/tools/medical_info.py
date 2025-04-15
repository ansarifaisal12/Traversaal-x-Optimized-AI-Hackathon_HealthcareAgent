import json
import os
import requests
import logging
from typing import Dict, List, Optional, Union, Any

from .base import LLMHealthTool

logger = logging.getLogger(__name__)

class MedicalInfoTool(LLMHealthTool):
    """
    Tool for retrieving reliable medical information.
    Uses Traversaal Ares API if available, otherwise falls back to LLM.
    """
    name: str = "Medical Info Tool"
    description: str = "retrieves reliable medical information about conditions, medications, and treatments"
    arg: str = "medical query string"
    ares_api_key: Optional[str] = None
    
    def __init__(self, **data):
        """Initialize the medical information tool."""
        super().__init__(**data)
        self.ares_api_key = os.environ.get("TRAVERSAAL_ARES_API_KEY", None)
        logger.info(f"Medical Info Tool initialized. Ares API available: {self.ares_api_key is not None}")
    
    def run(self, prompt: str) -> str:
        """
        Process medical information requests.
        
        Args:
            prompt: String query about medical information
            
        Returns:
            Response with reliable medical information
        """
        # Check if this is a sensitive medical query
        if self._is_sensitive_query(prompt):
            return self._get_sensitive_response(prompt)
        
        # If Ares API key is available, use it for up-to-date information
        if self.ares_api_key:
            return self._query_ares_api(prompt)
        
        # Otherwise, fall back to LLM-based information
        return self._get_llm_medical_info(prompt)
    
    def _is_sensitive_query(self, prompt: str) -> bool:
        """
        Check if the query is sensitive and requires special handling.
        Uses a simple keyword approach, but could be enhanced with more 
        advanced classification.
        """
        sensitive_keywords = [
            "diagnose", "diagnosis", "cancer", "terminal", "fatal", "emergency",
            "life-threatening", "critical", "urgent medical", "suicide", "self-harm"
        ]
        
        prompt_lower = prompt.lower()
        for keyword in sensitive_keywords:
            if keyword in prompt_lower:
                return True
        
        return False
    
    def _get_sensitive_response(self, prompt: str) -> str:
        """Generate an appropriate response for sensitive medical queries."""
        system_prompt = """
        You are a healthcare assistant responding to a potentially sensitive medical query.
        Always prioritize patient safety and wellbeing. For any serious medical concerns:
        
        1. Never provide a diagnosis
        2. Emphasize the importance of consulting a qualified healthcare professional
        3. Suggest appropriate next steps (e.g., calling a doctor, visiting urgent care)
        4. Provide general, factual information when safe to do so
        
        For emergencies, always advise seeking immediate medical attention.
        """
        
        sensitive_response = self.get_llm_response(prompt, system_prompt)
        return (
            "⚠️ This appears to be a sensitive medical question. While I can provide general information, "
            "I'm not qualified to provide medical diagnoses or emergency advice.\n\n"
            f"{sensitive_response}\n\n"
            "Please consult with a qualified healthcare professional for proper medical guidance."
        )
    
    def _query_ares_api(self, prompt: str) -> str:
        """
        Query the Traversaal Ares API for up-to-date medical information using the /live/predict endpoint.
        
        Args:
            prompt: Medical query string
            
        Returns:
            Response with medical information from Ares API
        """
        if not self.ares_api_key:
            logger.warning("Ares API key not available, falling back to LLM.")
            return self._get_llm_medical_info(prompt)
            
        url = "https://api-ares.traversaal.ai/live/predict"
        
        headers = {
            "x-api-key": self.ares_api_key,
            "content-type": "application/json"
        }
        
        # Payload according to the example, wrapping the query in a list
        payload = { "query": [prompt] }
        
        try:
            logger.info(f"Querying Traversaal Ares API /live/predict for: {prompt}")
            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                try:
                    results = response.json()
                    logger.info(f"Ares API successful response: {results}") # Log the raw response
                    
                    # Parse the /live/predict response format
                    formatted_response = "Here's what I found using the Traversaal medical AI:\n\n"
                    
                    # Check if response contains predictions
                    if isinstance(results, dict) and 'predictions' in results:
                        predictions = results['predictions']
                        
                        if isinstance(predictions, list) and predictions:
                            # Process each prediction
                            for prediction in predictions:
                                # Extract the prediction text directly
                                if isinstance(prediction, str):
                                    formatted_response += f"{prediction}\n\n"
                                # Or handle if prediction is structured as object
                                elif isinstance(prediction, dict):
                                    if 'text' in prediction:
                                        formatted_response += f"{prediction['text']}\n\n"
                                    elif 'answer' in prediction:
                                        formatted_response += f"{prediction['answer']}\n\n"
                                    else:
                                        # Fallback if structure is different
                                        formatted_response += f"{json.dumps(prediction)}\n\n"
                        elif isinstance(predictions, dict):
                            # Handle if predictions is a single dictionary
                            if 'text' in predictions:
                                formatted_response += f"{predictions['text']}\n\n"
                            elif 'answer' in predictions:
                                formatted_response += f"{predictions['answer']}\n\n"
                            else:
                                formatted_response += f"{json.dumps(predictions)}\n\n"
                        elif isinstance(predictions, str):
                            # Handle if predictions is directly a string
                            formatted_response += f"{predictions}\n\n"
                        else:
                            formatted_response += f"Raw predictions: {json.dumps(predictions)}\n\n"
                    else:
                        # Fallback for unexpected response format
                        formatted_response += f"Raw response: {json.dumps(results)}\n\n"

                    formatted_response += "Note: This information is for informational purposes and not a substitute for professional medical advice."
                    return formatted_response
                
                except json.JSONDecodeError:
                    logger.error(f"Ares API response was not valid JSON: {response.text}")
                    return self._get_llm_medical_info(prompt) # Fallback
                except Exception as parse_err:
                    logger.error(f"Error parsing Ares API response: {parse_err}. Raw response: {response.text}")
                    # Return raw response if parsing fails, but add disclaimer
                    return f"Received data from external search, but couldn't format it fully: {response.text}\n\nNote: This information is not a substitute for professional medical advice."
            else:
                logger.error(f"Ares API error: {response.status_code} - {response.text}")
                return self._get_llm_medical_info(prompt) # Fallback
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to Ares API: {str(e)}")
            return self._get_llm_medical_info(prompt) # Fallback
        except Exception as e:
            logger.error(f"Unexpected error during Ares API call: {str(e)}")
            return self._get_llm_medical_info(prompt) # Fallback
    
    def _get_llm_medical_info(self, prompt: str) -> str:
        """
        Get medical information using the LLM.
        
        Args:
            prompt: Medical query string
            
        Returns:
            Response with medical information from LLM
        """
        system_prompt = """
        You are a medical information assistant providing factual, evidence-based information.
        
        Guidelines:
        1. Provide accurate information based on current medical understanding
        2. Include disclaimers where appropriate
        3. Cite general sources of information when possible (e.g., "According to medical literature...")
        4. Avoid making definitive claims about treatments
        5. Never provide a diagnosis or suggest specific treatments
        6. Emphasize consulting healthcare professionals for medical advice
        
        Keep responses factual, balanced, and educational.
        """
        
        response = self.get_llm_response(prompt, system_prompt)
        
        # Add disclaimer
        disclaimer = (
            "\n\n*Note: This information is general in nature and should not replace professional "
            "medical advice. Always consult with qualified healthcare providers for personal medical concerns.*"
        )
        
        return response + disclaimer 