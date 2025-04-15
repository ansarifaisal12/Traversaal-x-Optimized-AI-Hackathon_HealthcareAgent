from openai import OpenAI
from typing import List, Dict, Any, Optional
import json
import os
from .tools.base import HealthTool
import logging
import google.generativeai as genai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEALTH_AGENT_SYSTEM_PROMPT = """
You are HealthGuard, an AI healthcare assistant designed to help patients manage their health.
You have access to the following specialized healthcare tools:

{tools}

Always prioritize patient safety and well-being. Never provide medical diagnoses or replace professional medical advice.
Instead, focus on:
1. Helping patients track their medications and symptoms
2. Providing reliable health information from trusted sources
3. Offering general wellness suggestions
4. Organizing and visualizing health data

For any serious health concerns, always recommend consulting a healthcare professional.

Use the following format:

Patient: the patient's question or request
Thought: carefully consider the appropriate action to take
Action: the action to take, should be one of [{tool_names}]
Action Input: the input for the tool
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat as needed)
Thought: I now know how to respond to the patient
Response: your helpful, empathetic response to the patient

Begin!
"""

class HealthGuardAgent:
    """
    HealthGuard AI Agent for healthcare assistance.
    Built on the AgentPro framework with specialized healthcare tools.
    """
    
    def __init__(self, 
                 llm=None, 
                 tools: List[HealthTool] = [], 
                 system_prompt: str = None, 
                 health_prompt: str = HEALTH_AGENT_SYSTEM_PROMPT,
                 patient_id: Optional[str] = None):
        """
        Initialize the HealthGuard Agent.
        
        Args:
            llm: Language model client (default: OpenAI client)
            tools: List of healthcare-specific tools
            system_prompt: Optional override for system prompt
            health_prompt: Healthcare-specific prompt template
            patient_id: Optional patient identifier for data persistence
        """
        self.llm_provider = "gemini"  # Default to Gemini
        
        # Check for available API keys and set provider
        if os.environ.get("GOOGLE_API_KEY"):
            self.llm_provider = "gemini"
            genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))
            self.gemini_client = genai
            logger.info("Agent using Google Gemini as LLM provider")
        elif os.environ.get("OPENAI_API_KEY"):
            self.llm_provider = "openai"
            self.client = llm if llm else OpenAI()
            logger.info("Agent using OpenAI as LLM provider")
        else:
            raise ValueError("Neither GOOGLE_API_KEY nor OPENAI_API_KEY environment variables are set")
            
        self.tools = self._format_tools(tools)
        self.health_prompt = health_prompt.format(
            tools="\n\n".join(map(lambda tool: tool.get_tool_description(), tools)),
            tool_names=", ".join(map(lambda tool: tool.name, tools)))
        self.messages = []
        
        if system_prompt:
            self.messages.append({"role": "system", "content": system_prompt})
        else:
            self.messages.append({"role": "system", "content": self.health_prompt})
        
        self.patient_id = patient_id
        logger.info(f"HealthGuard Agent initialized with {len(tools)} tools")
    
    def _format_tools(self, tools: List[HealthTool]) -> Dict:
        """Format tools into a name-indexed dictionary."""
        tool_names = list(map(lambda tool: tool.name, tools))
        return dict(zip(tool_names, tools))
    
    def _parse_action_string(self, text):
        """
        Parse agent's action and action input from the response text.
        Handles multi-line actions and observations.
        """
        lines = text.split('\n')
        action = None
        action_input = []
        is_action_input = False

        for line in lines:
            if line.startswith('Action:'):
                action = line.replace('Action:', '').strip()
                continue

            if line.startswith('Action Input:'):
                is_action_input = True
                input_text = line.replace('Action Input:', '').strip()
                if input_text:
                    action_input.append(input_text)
                continue

            if line.startswith('Observation:'):
                is_action_input = False
                continue

            # Collect multi-line action input
            if is_action_input and line.strip():
                action_input.append(line.strip())

        # Join multi-line action input
        action_input = '\n'.join(action_input)
        try:
            # Try to parse as JSON if possible
            action_input = json.loads(action_input)
        except Exception:
            # If not JSON, use as string
            pass
            
        return action, action_input

    def _tool_call(self, response):
        """Execute the tool specified in the agent's response."""
        action, action_input = self._parse_action_string(response)
        try:
            if action and action.strip().lower() in self.tools:
                tool_observation = self.tools[action.strip().lower()].run(action_input)
                return f"Observation: {tool_observation}"
            return f"Observation: Tool '{action}' not found. Available tools: {list(self.tools.keys())}"
        except Exception as e:
            logger.error(f"Error executing tool {action}: {str(e)}")
            return f"Observation: There was an error executing the tool.\nError: {str(e)}"

    def __call__(self, prompt):
        """
        Process a patient query and return a helpful response.
        
        Args:
            prompt: The patient's query or request
            
        Returns:
            The agent's final response
        """
        # Format patient message
        self.messages.append({"role": "user", "content": f"Patient: {prompt}"})
        
        try:
            # Interactive agent loop
            while True:
                # Get model response based on provider
                if self.llm_provider == "gemini":
                    response = self._get_gemini_response()
                else:
                    response = self._get_openai_response()
                
                # Add to conversation history
                self.messages.append({"role": "assistant", "content": response})
                
                # Check if final response is ready
                if "Response:" in response:
                    # Extract and return the final response
                    return response.split("Response:")[-1].strip()
                
                # Check if tool execution is needed
                if "Action:" in response and "Action Input:" in response:
                    # Execute tool and add result to conversation
                    observation = self._tool_call(response)
                    self.messages.append({"role": "user", "content": observation})
        
        except Exception as e:
            logger.error(f"Error in agent execution: {str(e)}")
            return f"I apologize, but I encountered a technical issue. Please try again or contact support if the problem persists."
    
    def _get_openai_response(self):
        """Get response from OpenAI model."""
        response = self.client.chat.completions.create(
            model="gpt-4o",  # Use GPT-4o for better medical understanding
            messages=self.messages,
            max_tokens=4000
        ).choices[0].message.content.strip()
        return response
    
    def _get_gemini_response(self):
        """Get response from Google Gemini model."""
        # Configure the generation config
        generation_config = {
            "temperature": 0.2,  # Low temperature for medical info
            "max_output_tokens": 4000,
        }
        
        # Convert OpenAI-style chat format to text for Gemini
        prompt_parts = []
        for message in self.messages:
            role = message["role"]
            content = message["content"]
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        # Join with double newlines to separate messages clearly
        full_prompt = "\n\n".join(prompt_parts)
        
        # Get model (using Gemini Pro)
        model = self.gemini_client.GenerativeModel('gemini-2.0-flash', 
                                                  generation_config=generation_config)
        
        # Generate response
        response = model.generate_content(full_prompt)
        
        # Return text response
        return response.text
    
    def get_conversation_history(self):
        """Return the full conversation history."""
        return self.messages
    
    def clear_conversation(self):
        """Clear the conversation history while keeping the system prompt."""
        system_prompt = self.messages[0]
        self.messages = [system_prompt]
        return "Conversation history cleared." 