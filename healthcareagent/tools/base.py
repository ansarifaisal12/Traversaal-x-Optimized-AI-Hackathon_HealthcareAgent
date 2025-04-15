from typing import Any, Dict, List, Optional, Union
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from openai import OpenAI
import os
import logging
import google.generativeai as genai

logger = logging.getLogger(__name__)

class HealthTool(ABC, BaseModel):
    """
    Base class for all healthcare-specific tools in the HealthGuard system.
    """
    name: str
    description: str
    arg: str
    
    def model_post_init(self, __context: Any) -> None:
        """Post-initialization processing to standardize tool properties."""
        self.name = self.name.lower().replace(' ', '_')
        self.description = self.description.lower()
        self.arg = self.arg.lower()
    
    @abstractmethod
    def run(self, prompt: Union[str, Dict]) -> str:
        """
        Execute the tool's functionality with the given input.
        
        Args:
            prompt: Input to the tool, either a string or a structured dictionary
            
        Returns:
            String result of the tool's operation
        """
        pass
    
    def get_tool_description(self) -> str:
        """Generate a standardized description of the tool for the agent."""
        return f"Tool: {self.name}\nDescription: {self.description}\nArg: {self.arg}"


class LLMHealthTool(HealthTool):
    """
    Health tool that uses a language model for enhanced capabilities.
    """
    client: Any = None
    gemini_client: Any = None
    llm_provider: str = "gemini"  # Default to Gemini
    
    def __init__(self, **data):
        """Initialize the LLM-powered health tool."""
        super().__init__(**data)
        
        # Set provider based on available API keys
        if os.environ.get("GOOGLE_API_KEY"):
            self.llm_provider = "gemini"
            genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
            self.gemini_client = genai
            logger.info("Using Google Gemini as LLM provider")
        elif os.environ.get("OPENAI_API_KEY"):
            self.llm_provider = "openai"
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            logger.info("Using OpenAI as LLM provider")
        else:
            raise ValueError("Neither GOOGLE_API_KEY nor OPENAI_API_KEY environment variables are set")
    
    def get_llm_response(self, prompt: str, system_prompt: str = None, temperature: float = 0.1) -> str:
        """
        Get a response from the language model.
        
        Args:
            prompt: User query or instruction
            system_prompt: Optional system prompt to guide the model
            temperature: Creativity parameter (0.0-1.0)
            
        Returns:
            Model's response text
        """
        try:
            if self.llm_provider == "gemini":
                return self._get_gemini_response(prompt, system_prompt, temperature)
            else:
                return self._get_openai_response(prompt, system_prompt, temperature)
        except Exception as e:
            logger.error(f"Error getting LLM response: {str(e)}")
            return f"Error: Unable to get AI response. {str(e)}"
    
    def _get_openai_response(self, prompt: str, system_prompt: str = None, temperature: float = 0.1) -> str:
        """Get response from OpenAI."""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=temperature,
            max_tokens=2000
        )
        return response.choices[0].message.content
    
    def _get_gemini_response(self, prompt: str, system_prompt: str = None, temperature: float = 0.1) -> str:
        """Get response from Google Gemini."""
        # Configure the generation config
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": 2000,
        }
        
        # For Gemini, combine system prompt and user prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\nUser query: {prompt}"
        else:
            full_prompt = prompt
        
        # Get model (using Gemini Pro which is most similar to GPT-4)
        model = self.gemini_client.GenerativeModel('gemini-2.0-flash', 
                                                  generation_config=generation_config)
        
        # Generate response
        response = model.generate_content(full_prompt)
        
        # Return text response
        return response.text 